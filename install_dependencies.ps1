# Quick Dependency Installation Script
# Run this before training the model

Write-Host "Installing dependencies for hotel email parser..." -ForegroundColor Green

# Check if Poetry is available
$poetryAvailable = Get-Command poetry -ErrorAction SilentlyContinue

if ($poetryAvailable) {
    Write-Host "`nUsing Poetry to install dependencies..." -ForegroundColor Cyan
    poetry install
} else {
    Write-Host "`nPoetry not found. Installing with pip..." -ForegroundColor Yellow
    pip install transformers torch scikit-learn matplotlib seaborn tqdm pyyaml
}

Write-Host "`nDependencies installed! You can now run:" -ForegroundColor Green
Write-Host "  python scripts\train_intent_classifier.py" -ForegroundColor White
