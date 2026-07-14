# Number Verification 3-legged flow probe (docs/08 §1a, gate doc 02 open question).
# Walks: client credentials -> OIDC discovery -> authorize redirect chain (captures
# the auth code from Location headers, no callback server needed) -> token exchange
# -> Bearer-authorized NV verify + device-phone-number.
# Secrets/codes/tokens are printed MASKED only.
# Usage: powershell -ExecutionPolicy Bypass -File nv_flow_probe.ps1
$ErrorActionPreference = 'Continue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$envPath = Join-Path $PSScriptRoot '.env'
$cfg = @{}
foreach ($line in Get-Content $envPath) {
    $line = $line.Trim()
    if ($line -and -not $line.StartsWith('#') -and $line.Contains('=')) {
        $k, $v = $line -split '=', 2; $cfg[$k.Trim()] = $v.Trim()
    }
}
$KEY   = $cfg['RAPIDAPI_KEY']
$BASE  = if ($cfg['NAC_BASE_URL']) { $cfg['NAC_BASE_URL'] } else { 'https://network-as-code.p-eu.rapidapi.com' }
$HOSTH = if ($cfg['NAC_RAPIDAPI_HOST']) { $cfg['NAC_RAPIDAPI_HOST'] } else { 'network-as-code.nokia.rapidapi.com' }
$PHONE = '+99999991000'   # docs example persona
$REDIRECT = 'https://example.com/redirect'
$rapid = @{ 'X-RapidAPI-Key' = $KEY; 'X-RapidAPI-Host' = $HOSTH }
function Mask($s) { if (-not $s) { '(empty)' } elseif ($s.Length -le 8) { '****' } else { $s.Substring(0,6) + '...(' + $s.Length + ' chars)' } }

# 1. client credentials -------------------------------------------------------
$cc = Invoke-RestMethod -Uri ($BASE + '/oauth2/v1/auth/clientcredentials') -Headers $rapid -TimeoutSec 30
Write-Host ("1. client_id=" + (Mask $cc.client_id) + "  client_secret=(hidden)")

# 2. discovery ----------------------------------------------------------------
$oidc = Invoke-RestMethod -Uri ($BASE + '/.well-known/openid-configuration') -Headers $rapid -TimeoutSec 30
Write-Host ("2. authorize=" + $oidc.authorization_endpoint + "  token=" + $oidc.token_endpoint)

# 3. authorize redirect chain --------------------------------------------------
$scope = [uri]::EscapeDataString('dpv:FraudPreventionAndDetection number-verification:verify')
$login = [uri]::EscapeDataString($PHONE)
$redir = [uri]::EscapeDataString($REDIRECT)
$url = "$($oidc.authorization_endpoint)?scope=$scope&response_type=code&client_id=$($cc.client_id)&redirect_uri=$redir&login_hint=$login&state=spike123"
$code = $null
$cookies = New-Object Net.CookieContainer
for ($hop = 1; $hop -le 8 -and -not $code; $hop++) {
    $status = $null; $loc = $null; $bodySnippet = ''
    try {
        $req = [Net.WebRequest]::CreateHttp($url)
        $req.AllowAutoRedirect = $false
        $req.CookieContainer = $cookies
        $req.Timeout = 30000
        try {
            $resp = $req.GetResponse()
        } catch [Net.WebException] {
            if ($_.Exception.Response) { $resp = $_.Exception.Response } else { throw }
        }
        $status = [int]$resp.StatusCode
        $loc = $resp.Headers['Location']
        try { $bodySnippet = ((New-Object IO.StreamReader($resp.GetResponseStream())).ReadToEnd() -replace '\s+', ' ') } catch {}
        if ($bodySnippet.Length -gt 220) { $bodySnippet = $bodySnippet.Substring(0, 220) }
        $resp.Close()
    } catch {
        Write-Host ("3.$hop EXC " + $_.Exception.Message); break
    }
    $locShown = if ($loc) { ($loc -replace 'code=[^&]+', 'code=****') } else { '(none)' }
    Write-Host ("3.$hop status=$status  location=$locShown")
    # only OUR redirect_uri terminates the chain - inner hops carry Nokia's own PKCE codes
    if ($loc -and $loc.StartsWith($REDIRECT) -and $loc -match 'code=([^&]+)') { $code = $Matches[1]; break }
    if ($loc -and $loc.StartsWith($REDIRECT)) { Write-Host '3.x reached redirect_uri without code'; break }
    if ($loc) {
        if ($loc.StartsWith('/')) { $u = [uri]$url; $url = $u.Scheme + '://' + $u.Host + $loc } else { $url = $loc }
    } else {
        Write-Host ("3.x no redirect; body: " + $bodySnippet)
        break
    }
}
if (-not $code) { Write-Host 'RESULT: no auth code obtained — see chain above.'; exit 1 }
Write-Host ("4. auth code obtained: " + (Mask $code))

# 5. token exchange ------------------------------------------------------------
$tokenBody = @{ client_id = $cc.client_id; client_secret = $cc.client_secret; grant_type = 'authorization_code'; code = $code; redirect_uri = $REDIRECT }
try {
    $tok = Invoke-RestMethod -Uri $oidc.token_endpoint -Method POST -Body $tokenBody -TimeoutSec 30
    Write-Host ("5. access_token=" + (Mask $tok.access_token) + "  type=" + $tok.token_type)
} catch {
    $resp = $_.Exception.Response; $b = ''
    if ($resp) { try { $b = (New-Object IO.StreamReader($resp.GetResponseStream())).ReadToEnd() } catch {} }
    Write-Host ("5. TOKEN EXCHANGE FAILED: " + $b); exit 1
}

# 6. NV verify with Bearer -------------------------------------------------------
$h6 = @{ 'X-RapidAPI-Key' = $KEY; 'X-RapidAPI-Host' = $HOSTH; 'Authorization' = ('Bearer ' + $tok.access_token); 'Content-Type' = 'application/json' }
try {
    $v = Invoke-RestMethod -Uri ($BASE + '/passthrough/camara/v1/number-verification/number-verification/v0/verify') -Method POST -Headers $h6 -Body (@{ phoneNumber = $PHONE } | ConvertTo-Json) -TimeoutSec 30
    Write-Host ("6. NV VERIFY: " + ($v | ConvertTo-Json -Compress))
} catch {
    $resp = $_.Exception.Response; $b = ''
    if ($resp) { try { $b = (New-Object IO.StreamReader($resp.GetResponseStream())).ReadToEnd() } catch {} }
    Write-Host ("6. NV VERIFY FAILED: " + [int]$resp.StatusCode + " " + $b)
}

# 7. device-phone-number ---------------------------------------------------------
try {
    $p = Invoke-RestMethod -Uri ($BASE + '/passthrough/camara/v1/number-verification/number-verification/v0/device-phone-number') -Method GET -Headers $h6 -TimeoutSec 30
    Write-Host ("7. DEVICE PHONE: " + ($p | ConvertTo-Json -Compress))
} catch {
    Write-Host "7. device-phone-number failed (may need a fresh single-use token - acceptable)"
}
