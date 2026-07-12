# Persona probe — maps every official NaC simulator number across the demo-relevant
# APIs to discover each number's canned behavior ("persona"). Results ->
# persona-matrix.json + compact console table. Read-only calls.
# Usage: powershell -ExecutionPolicy Bypass -File persona_probe.ps1
$ErrorActionPreference = 'Continue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$envPath = Join-Path $PSScriptRoot '.env'
$cfg = @{}
if (Test-Path $envPath) {
    foreach ($line in Get-Content $envPath) {
        $line = $line.Trim()
        if ($line -and -not $line.StartsWith('#') -and $line.Contains('=')) {
            $k, $v = $line -split '=', 2; $cfg[$k.Trim()] = $v.Trim()
        }
    }
}
$KEY   = $cfg['RAPIDAPI_KEY']
$BASE  = if ($cfg['NAC_BASE_URL']) { $cfg['NAC_BASE_URL'] } else { 'https://network-as-code.p-eu.rapidapi.com' }
$HOSTH = if ($cfg['NAC_RAPIDAPI_HOST']) { $cfg['NAC_RAPIDAPI_HOST'] } else { 'network-as-code.nokia.rapidapi.com' }
if (-not $KEY) { Write-Error 'RAPIDAPI_KEY missing'; exit 1 }
$headers = @{ 'X-RapidAPI-Key' = $KEY; 'X-RapidAPI-Host' = $HOSTH; 'Content-Type' = 'application/json' }

# Official simulator roster (portal API overview, Jul 2026)
$numbers = @('+99999991000','+99999991001','+99999990400','+99999990404','+99999990422',
             '+99999990500','+99999990502','+99999990503','+99999990504')

# Budapest-area circle (the simulators' home per docs example)
$bud = @{ areaType='CIRCLE'; center=@{ latitude=47.44178899529922; longitude=19.160422047462603 }; radius=50000 }

function Call($path, $body) {
    try {
        $r = Invoke-WebRequest -Uri ($BASE + $path) -Method POST -Headers $headers `
              -Body ($body | ConvertTo-Json -Depth 8) -UseBasicParsing -TimeoutSec 20
        return @{ s = [int]$r.StatusCode; j = ($r.Content | ConvertFrom-Json) ; raw = $r.Content }
    } catch {
        $resp = $_.Exception.Response
        if ($resp) {
            $b = ''; try { $b = (New-Object IO.StreamReader($resp.GetResponseStream())).ReadToEnd() } catch {}
            return @{ s = [int]$resp.StatusCode; j = $null; raw = $b }
        }
        return @{ s = 'EXC'; j = $null; raw = $_.Exception.Message }
    }
}
function Fmt($r, $script) { if ($r.s -eq 200) { & $script $r.j } else { "[$($r.s)]" } }

$matrix = [ordered]@{}
foreach ($n in $numbers) {
    $dev = @{ phoneNumber = $n }
    $row = [ordered]@{}
    $row['sim_swap']   = Call '/passthrough/camara/v1/sim-swap/sim-swap/v0/check' @{ phoneNumber=$n; maxAge=240 }
    $row['dev_swap']   = Call '/passthrough/camara/v1/device-swap/device-swap/v1/check' @{ phoneNumber=$n; maxAge=240 }
    $row['fwd']        = Call '/passthrough/camara/v1/call-forwarding-signal/call-forwarding-signal/v0.3/unconditional-call-forwardings' @{ phoneNumber=$n }
    $row['recycled']   = Call '/passthrough/camara/v1/number-recycling/number-recycling/v0.2/check' @{ phoneNumber=$n; specifiedDate='2025-01-01' }
    $row['tenure']     = Call '/passthrough/camara/v1/kyc-tenure/kyc-tenure/v0.1/check-tenure' @{ phoneNumber=$n; tenureDate='2023-01-01' }
    $row['conn']       = Call '/device-status/v0/connectivity' @{ device=$dev }
    $row['roam']       = Call '/device-status/device-roaming-status/v1/retrieve' @{ device=$dev }
    $row['loc']        = Call '/location-retrieval/v0/retrieve' @{ device=$dev; maxAge=3600 }
    $row['verify_bud'] = Call '/location-verification/v1/verify' @{ device=$dev; area=$bud; maxAge=3600 }
    $matrix[$n] = $row

    $line = "{0}: swap={1} devswap={2} fwd={3} rec={4} ten={5} conn={6} roam={7} verifyBUD={8} loc={9}" -f $n,
        (Fmt $row['sim_swap']   { param($j) $j.swapped }),
        (Fmt $row['dev_swap']   { param($j) $j.swapped }),
        (Fmt $row['fwd']        { param($j) $j.active }),
        (Fmt $row['recycled']   { param($j) $j.phoneNumberRecycled }),
        (Fmt $row['tenure']     { param($j) $j.tenureDateCheck }),
        (Fmt $row['conn']       { param($j) $j.connectivityStatus }),
        (Fmt $row['roam']       { param($j) if ($j.roaming) { "true($($j.countryCode))" } else { 'false' } }),
        (Fmt $row['verify_bud'] { param($j) $j.verificationResult }),
        (Fmt $row['loc']        { param($j) "{0:N2},{1:N2}" -f $j.area.center.latitude, $j.area.center.longitude })
    Write-Host $line
    Start-Sleep -Milliseconds 150
}

# strip parsed objects for json output (keep status + raw)
$out = [ordered]@{}
foreach ($n in $matrix.Keys) {
    $out[$n] = [ordered]@{}
    foreach ($api in $matrix[$n].Keys) { $out[$n][$api] = @{ status = $matrix[$n][$api].s; body = $matrix[$n][$api].raw } }
}
$dst = Join-Path $PSScriptRoot 'persona-matrix.json'
$out | ConvertTo-Json -Depth 5 | Out-File -Encoding utf8 $dst
Write-Host "`nFull matrix -> $dst"
