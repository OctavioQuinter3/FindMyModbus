$name = "FindMyModbus"
$dist = "dist"
if (Test-Path $dist) { Remove-Item -LiteralPath $dist -Recurse -Force -ErrorAction SilentlyContinue }

python -m PyInstaller --onedir --noconsole --noconfirm `
    --name $name `
    --distpath $dist `
    --hidden-import "pymodbus" `
    --hidden-import "pymodbus.client" `
    --hidden-import "pymodbus.client.serial" `
    --hidden-import "pymodbus.client.tcp" `
    --hidden-import "serial" `
    --hidden-import "serial.tools.list_ports" `
    --collect-all "customtkinter" `
    main.py

if ($?) {
    Remove-Item -Recurse -Force "build", "$name.spec" -ErrorAction SilentlyContinue
    $exe = Get-ChildItem "$dist\$name\$name.exe"
    $size = [math]::Round($exe.Length / 1MB, 1)
    Write-Host "`nOK  $size MB  $($exe.FullName)"
} else {
    Write-Host "Build FAILED"
}
