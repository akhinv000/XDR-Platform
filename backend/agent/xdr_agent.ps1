<#
.SYNOPSIS
    XDR BASE - Lightweight Windows Endpoint Telemetry & Containment Agent
    Streams Windows Security Events (4625, 4624, 4688) & supports automated quarantine.
#>

$ConfigFile = Join-Path $PSScriptRoot "config.json"
$TokenFile = Join-Path $PSScriptRoot "agent_token.json"

$ServerUrl = "http://127.0.0.1:9000"
$HeartbeatInterval = 15

if (Test-Path $ConfigFile) {
    try {
        $Config = Get-Content $ConfigFile | ConvertFrom-Json
        if ($Config.server_url) { $ServerUrl = $Config.server_url.TrimEnd('/') }
        if ($Config.heartbeat_interval) { $HeartbeatInterval = [int]$Config.heartbeat_interval }
    } catch {
        Write-Warning "Failed to parse config.json"
    }
}

function Get-LocalIP {
    try {
        $ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notmatch 'Loopback' -and $_.IPAddress -notmatch '^169\.' } | Select-Object -First 1).IPAddress
        if ($ip) { return $ip }
    } catch {}
    return "127.0.0.1"
}

# 1. Register or Load Token
$AgentId = $null
$ApiKey = $null

if (Test-Path $TokenFile) {
    try {
        $tokenData = Get-Content $TokenFile | ConvertFrom-Json
        $AgentId = $tokenData.agent_id
        $ApiKey = $tokenData.api_key
        Write-Host "[*] Loaded existing Agent ID: $AgentId" -ForegroundColor Cyan
    } catch {}
}

if (-not $AgentId) {
    $Hostname = $env:COMPUTERNAME
    $IP = Get-LocalIP
    $OS = (Get-CimInstance Win32_OperatingSystem).Caption

    Write-Host "[*] Registering Windows Endpoint '$Hostname' ($IP) with $ServerUrl..." -ForegroundColor Cyan
    $body = @{
        hostname = $Hostname
        ip_address = $IP
        operating_system = "Windows"
        os_version = $OS
        mac_address = ""
    } | ConvertTo-Json

    try {
        $res = Invoke-RestMethod -Uri "$ServerUrl/api/v1/agent/register" -Method Post -Body $body -ContentType "application/json"
        $AgentId = $res.agent_id
        $ApiKey = $res.api_key
        @{ agent_id = $AgentId; api_key = $ApiKey } | ConvertTo-Json | Set-Content $TokenFile
        Write-Host "[+] Successfully registered! Agent ID: $AgentId" -ForegroundColor Green
    } catch {
        Write-Error "[-] Failed to register agent with server: $_"
        Exit 1
    }
}

# 2. Containment Action Handlers
function Quarantine-Host {
    Write-Warning "[!] ISOLATING HOST FROM NETWORK..."
    try {
        netsh advfirewall firewall add rule name="XDR_ISOLATE_IN" dir=in action=block
        netsh advfirewall firewall add rule name="XDR_ISOLATE_OUT" dir=out action=block
        netsh advfirewall firewall add rule name="XDR_ALLOW_OUT" dir=out action=allow remoteport=9000 protocol=TCP
        Write-Host "[+] Windows Firewall containment rules active." -ForegroundColor Red
    } catch {
        Write-Error "[-] Quarantine failed: $_"
    }
}

function Unquarantine-Host {
    Write-Host "[*] Restoring network connectivity..." -ForegroundColor Green
    try {
        netsh advfirewall firewall delete rule name="XDR_ISOLATE_IN"
        netsh advfirewall firewall delete rule name="XDR_ISOLATE_OUT"
        netsh advfirewall firewall delete rule name="XDR_ALLOW_OUT"
        Write-Host "[+] Full network connectivity restored." -ForegroundColor Green
    } catch {
        Write-Error "[-] Unquarantine failed: $_"
    }
}

function Block-IPAddress($IP) {
    Write-Warning "[!] Blocking IP: $IP"
    try {
        netsh advfirewall firewall add rule name="XDR_BLOCK_$IP" dir=in action=block remoteip=$IP
    } catch {}
}

# 3. Main Heartbeat & Monitoring Loop
Write-Host "[+] XDR Windows Agent monitoring active. Heartbeat every ${HeartbeatInterval}s." -ForegroundColor Green

$lastEventCheck = (Get-Date).AddMinutes(-5)

while ($true) {
    # Send Heartbeat
    try {
        $hbBody = @{
            agent_id = $AgentId
            cpu_percent = 0.0
            memory_percent = 0.0
            disk_percent = 0.0
            active_connections = 0
        } | ConvertTo-Json

        $headers = @{ "X-Agent-Key" = $ApiKey }
        $hbRes = Invoke-RestMethod -Uri "$ServerUrl/api/v1/agent/heartbeat" -Method Post -Body $hbBody -Headers $headers -ContentType "application/json"

        if ($hbRes.commands) {
            foreach ($cmd in $hbRes.commands) {
                if ($cmd.action -eq "quarantine") { Quarantine-Host }
                elseif ($cmd.action -eq "unquarantine") { Unquarantine-Host }
                elseif ($cmd.action -eq "block_ip") { Block-IPAddress $cmd.ip }
            }
        }
    } catch {
        Write-Warning "[!] Heartbeat failure: $_"
    }

    # Query recent security events (4625: Failed logon, 4624: Logon, 4688: Process creation)
    try {
        $events = Get-WinEvent -FilterHashtable @{ LogName='Security'; Id=4625, 4688; StartTime=$lastEventCheck } -ErrorAction SilentlyContinue -MaxEvents 20
        $lastEventCheck = Get-Date

        if ($events) {
            $telemetryEvents = @()
            foreach ($ev in $events) {
                $telemetryEvents += @{
                    message = "EventID=$($ev.Id) Host=$($env:COMPUTERNAME) Message=$($ev.Message -replace "`r`n", " ")"
                    source = "WinSecurity"
                    level = if ($ev.Id -eq 4625) { "High" } else { "Low" }
                    timestamp = $ev.TimeCreated.ToString("o")
                }
            }

            $telemBody = @{
                agent_id = $AgentId
                events = $telemetryEvents
            } | ConvertTo-Json -Depth 4

            Invoke-RestMethod -Uri "$ServerUrl/api/v1/agent/telemetry" -Method Post -Body $telemBody -Headers @{ "X-Agent-Key" = $ApiKey } -ContentType "application/json" | Out-Null
        }
    } catch {}

    Start-Sleep -Seconds $HeartbeatInterval
}
