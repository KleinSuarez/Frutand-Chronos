# Script de firma digital en almacén personal
$cert = New-SelfSignedCertificate -Subject "CN=Frutand S.A.S." -Type CodeSigningCert -CertStoreLocation "Cert:\CurrentUser\My"
$exePath = "c:\Users\yahir\Code\Frutand Chronos\project\dist\FrutandChronos\FrutandChronos.exe"

if (Test-Path $exePath) {
    $sig = Set-AuthenticodeSignature -FilePath $exePath -Certificate $cert
    Write-Host "Estado de Firma:" $sig.Status
    Write-Host "Firmante:" $sig.SignerCertificate.Subject
}
