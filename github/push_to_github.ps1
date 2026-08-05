# push_to_github.ps1
# Developer script to safely push the core RAG Engine to GitHub.

Write-Host "Checking formatting with Ruff (if installed)..." -ForegroundColor Cyan
if (Get-Command ruff -ErrorAction SilentlyContinue) {
    ruff format .
    ruff check . --fix
} else {
    Write-Host "Ruff not found. Skipping auto-formatting." -ForegroundColor Yellow
}

Write-Host "Staging files (Data is protected by .gitignore)..." -ForegroundColor Cyan
git add .

Write-Host "Committing..." -ForegroundColor Cyan
$commitMessage = Read-Host "Enter commit message (Press Enter for 'Update engine architecture')"
if ([string]::IsNullOrWhiteSpace($commitMessage)) {
    $commitMessage = "Update engine architecture"
}
git commit -m $commitMessage

Write-Host "Pushing to GitHub..." -ForegroundColor Cyan
# Uses the origin remote configured in your local git
git push origin master

Write-Host "Done!" -ForegroundColor Green
