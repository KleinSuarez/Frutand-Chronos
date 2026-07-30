# Script de Instalación Automática de Certificado Frutand S.A.S.
# Ejecutar haciendo clic derecho -> "Ejecutar con PowerShell"

$exePath = Join-Path $PSScriptRoot "FrutandChronos.exe"
$cerPath = Join-Path $PSScriptRoot "FrutandSAS.cer"

if (Test-Path $exePath) {
    $sig = Get-AuthenticodeSignature $exePath
    if ($sig.SignerCertificate) {
        $cert = $sig.SignerCertificate
        $store = New-Object System.Security.Cryptography.X509Certificates.X509Store("Root", "CurrentUser")
        $store.Open("ReadWrite")
        $store.Add($cert)
        $store.Close()
        Write-Host "✅ El certificado de Frutand S.A.S. ha sido instalado y confiado exitosamente en este equipo." -ForegroundColor Green
    } else {
        Write-Host "⚠️ No se encontró una firma en $exePath" -ForegroundColor Yellow
    }
} elseif (Test-Path $cerPath) {
    Import-Certificate -FilePath $cerPath -CertStoreLocation "Cert:\CurrentUser\Root" | Out-Null
    Write-Host "✅ El certificado FrutandSAS.cer ha sido instalado exitosamente." -ForegroundColor Green
} else {
    Write-Host "❌ No se encontró FrutandChronos.exe ni FrutandSAS.cer en la carpeta." -ForegroundColor Red
}

Start-Sleep -Seconds 3
