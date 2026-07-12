# NaC API spike — PowerShell variant (no Python required).
# Same endpoints as nac_spike.py; results -> spike-results.json.
# Usage:  powershell -ExecutionPolicy Bypass -File nac_spike.ps1 [-Mutations]
param([switch]$Mutations)

$ErrorActionPreference = 'Continue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# --- load .env (never print values) ---------------------------------------
$envPath = Join-Path $PSScriptRoot '.env'
$cfg = @{}
if (Test-Path $envPath) {
    foreach ($line in Get-Content $envPath) {
        $line = $line.Trim()
        if ($line -and -not $line.StartsWith('#') -and $line.Contains('=')) {
            $k, $v = $line -split '=', 2
            $cfg[$k.Trim()] = $v.Trim()
        }
    }
}
function Get-Cfg($key, $default) { if ($cfg.ContainsKey($key) -and $cfg[$key]) { $cfg[$key] } else { $default } }

$KEY   = Get-Cfg 'RAPIDAPI_KEY' ''
$BASE  = Get-Cfg 'NAC_BASE_URL' 'https://network-as-code.p-eu.rapidapi.com'
$HOSTH = Get-Cfg 'NAC_RAPIDAPI_HOST' 'network-as-code.nokia.rapidapi.com'
$PHONE = Get-Cfg 'DEVICE_PHONE' '+99999991000'   # roster personas: see .env.example
$SINK  = Get-Cfg 'SINK_URL' 'https://example.com/nac-sink'
if (-not $KEY) { Write-Error 'RAPIDAPI_KEY missing in backend/spike/.env'; exit 1 }

$headers = @{ 'X-RapidAPI-Key' = $KEY; 'X-RapidAPI-Host' = $HOSTH; 'Content-Type' = 'application/json' }
$device  = @{ phoneNumber = $PHONE }
$area    = @{ areaType = 'CIRCLE'; center = @{ latitude = 25.276987; longitude = 55.296249 }; radius = 2000 }

function Invoke-Nac($name, $path, $body, $method = 'POST') {
    $uri = $BASE + $path
    try {
        $json = if ($null -ne $body) { $body | ConvertTo-Json -Depth 8 } else { $null }
        $resp = Invoke-WebRequest -Uri $uri -Method $method -Headers $headers -Body $json -UseBasicParsing -TimeoutSec 30
        $status = [int]$resp.StatusCode; $content = $resp.Content
    } catch {
        $r = $_.Exception.Response
        if ($r) {
            $status = [int]$r.StatusCode
            try { $content = (New-Object IO.StreamReader($r.GetResponseStream())).ReadToEnd() } catch { $content = '' }
        } else { $status = 'EXCEPTION'; $content = $_.Exception.Message }
    }
    $preview = if ($content) { ($content -replace '\s+', ' ').Substring(0, [Math]::Min(160, $content.Length)) } else { '' }
    Write-Host ("{0,-34} -> {1}  {2}" -f $name, $status, $preview)
    return @{ status = $status; body = $content }
}

$results = [ordered]@{ _meta = @{ ts = (Get-Date).ToUniversalTime().ToString('o'); base = $BASE; phone = $PHONE; mutations = [bool]$Mutations } }

$calls = [ordered]@{
    'sim_swap_check'                = @('/passthrough/camara/v1/sim-swap/sim-swap/v0/check', @{ phoneNumber = $PHONE; maxAge = 240 })
    'sim_swap_retrieve_date'        = @('/passthrough/camara/v1/sim-swap/sim-swap/v0/retrieve-date', @{ phoneNumber = $PHONE })
    'device_swap_check'             = @('/passthrough/camara/v1/device-swap/device-swap/v1/check', @{ phoneNumber = $PHONE; maxAge = 240 })
    'reachability'                  = @('/device-status/device-reachability-status/v1/retrieve', @{ device = $device })
    'roaming'                       = @('/device-status/device-roaming-status/v1/retrieve', @{ device = $device })
    'connectivity'                  = @('/device-status/v0/connectivity', @{ device = $device })
    'location_retrieve'             = @('/location-retrieval/v0/retrieve', @{ device = $device; maxAge = 3600 })
    'location_verify'               = @('/location-verification/v1/verify', @{ device = $device; area = $area })
    'congestion_query'              = @('/congestion-insights/v0/query', @{ device = $device })
    'tenure_check'                  = @('/passthrough/camara/v1/kyc-tenure/kyc-tenure/v0.1/check-tenure', @{ phoneNumber = $PHONE; tenureDate = '2023-01-01' })
    'number_recycling_check'        = @('/passthrough/camara/v1/number-recycling/number-recycling/v0.2/check', @{ phoneNumber = $PHONE; specifiedDate = '2025-01-01' })
    'call_forwarding_unconditional' = @('/passthrough/camara/v1/call-forwarding-signal/call-forwarding-signal/v0.3/unconditional-call-forwardings', @{ phoneNumber = $PHONE })
    'kyc_match_minimal'             = @('/passthrough/camara/v1/kyc-match/kyc-match/v0.3/match', @{ phoneNumber = $PHONE; name = 'Test User'; birthdate = '1990-01-01' })
    'age_verification'              = @('/passthrough/camara/v1/kyc-age-verification/kyc-age-verification/v0.1/verify', @{ phoneNumber = $PHONE; ageThreshold = 18 })
    'number_verification_no_code'   = @('/passthrough/camara/v1/number-verification/number-verification/v0/verify', @{ phoneNumber = $PHONE })
}
foreach ($name in $calls.Keys) {
    $results[$name] = Invoke-Nac $name $calls[$name][0] $calls[$name][1]
}

if ($Mutations) {
    # QoD is flow-oriented: device MUST carry an ipv4Address (confirmed Jul 7 — 400 without, 201 with)
    $qod = Invoke-Nac 'qod_create' '/qod/v0/sessions' @{
        qosProfile = 'QOS_E'
        device = @{ phoneNumber = $PHONE; ipv4Address = @{ publicAddress = '1.1.1.2'; privateAddress = '1.1.1.2' } }
        applicationServer = @{ ipv4Address = '5.6.7.8' }; duration = 60
    }
    $results['qod_create'] = $qod
    try { $sid = ($qod.body | ConvertFrom-Json).sessionId } catch { $sid = $null }
    if ($sid) { $results['qod_delete'] = Invoke-Nac 'qod_delete' "/qod/v0/sessions/$sid" $null 'DELETE' }

    $geo = Invoke-Nac 'geofence_create' '/geofencing-subscriptions/v0.3/subscriptions' @{
        protocol = 'HTTP'; sink = $SINK
        types    = @('org.camaraproject.geofencing-subscriptions.v0.area-entered')
        config   = @{
            subscriptionDetail    = @{ device = $device; area = $area }
            initialEvent          = $true
            subscriptionMaxEvents = 5
            subscriptionExpireTime = (Get-Date).ToUniversalTime().AddHours(1).ToString("yyyy-MM-dd'T'HH:mm:ss'Z'")
        }
    }
    $results['geofence_create'] = $geo
    try { $gid = ($geo.body | ConvertFrom-Json).id } catch { $gid = $null }
    if ($gid) { $results['geofence_delete'] = Invoke-Nac 'geofence_delete' "/geofencing-subscriptions/v0.3/subscriptions/$gid" $null 'DELETE' }
}

$out = Join-Path $PSScriptRoot 'spike-results.json'
$results | ConvertTo-Json -Depth 6 | Out-File -Encoding utf8 $out
Write-Host "`nRaw results -> $out"
