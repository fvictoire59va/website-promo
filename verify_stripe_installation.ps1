# Script PowerShell de vérification de l'installation Stripe

Write-Host "═════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "🔍 VÉRIFICATION DE L'INSTALLATION STRIPE" -ForegroundColor Cyan
Write-Host "═════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$checkStatus = 0

# 1. Vérifier les fichiers créés
Write-Host "1️⃣  Vérification des fichiers..." -ForegroundColor Yellow
Write-Host ""

$filesToCheck = @(
    "stripe_integration\__init__.py",
    "stripe_integration\stripe_config.py",
    "stripe_integration\payment_service.py",
    "stripe_integration\endpoints.py",
    "test\__init__.py",
    "test\test_payment.py",
    "test\README.md",
    "STRIPE_SETUP_GUIDE.md",
    "STRIPE_INDEX.md",
    "MONETISATION_SUMMARY.md",
    "PAYMENT_INTEGRATION_EXAMPLE.py",
    "GIT_WORKFLOW.md"
)

foreach ($file in $filesToCheck) {
    if (Test-Path $file) {
        Write-Host "✓ $file" -ForegroundColor Green
    } else {
        Write-Host "✗ $file (MANQUANT)" -ForegroundColor Red
        $checkStatus = 1
    }
}

Write-Host ""

# 2. Vérifier les dépendances
Write-Host "2️⃣  Vérification des dépendances dans requirements.txt..." -ForegroundColor Yellow
Write-Host ""

$deps = @(
    "stripe>=7.0.0",
    "pytest>=7.0.0",
    "python-dotenv>=1.0.0",
    "pytest-asyncio>=0.21.0"
)

$requirementsContent = Get-Content requirements.txt -Raw

foreach ($dep in $deps) {
    if ($requirementsContent -match $dep) {
        Write-Host "✓ $dep" -ForegroundColor Green
    } else {
        Write-Host "✗ $dep (MANQUANT)" -ForegroundColor Red
        $checkStatus = 1
    }
}

Write-Host ""

# 3. Vérifier la structure des répertoires
Write-Host "3️⃣  Vérification de la structure des répertoires..." -ForegroundColor Yellow
Write-Host ""

if (Test-Path "stripe_integration") {
    $fileCount = (Get-ChildItem -Path "stripe_integration" -Recurse -File).Count
    Write-Host "✓ stripe_integration\ ($fileCount fichiers)" -ForegroundColor Green
} else {
    Write-Host "✗ stripe_integration\ (RÉPERTOIRE MANQUANT)" -ForegroundColor Red
    $checkStatus = 1
}

if (Test-Path "test") {
    $fileCount = (Get-ChildItem -Path "test" -Recurse -File).Count
    Write-Host "✓ test\ ($fileCount fichiers)" -ForegroundColor Green
} else {
    Write-Host "✗ test\ (RÉPERTOIRE MANQUANT)" -ForegroundColor Red
    $checkStatus = 1
}

Write-Host ""

# 4. Vérifier que .env n'est pas commité
Write-Host "4️⃣  Vérification de la sécurité..." -ForegroundColor Yellow
Write-Host ""

if (Test-Path ".env") {
    Write-Host "⚠  .env existe (vérifier qu'il n'est pas commité)" -ForegroundColor Yellow
    
    if (Test-Path ".gitignore") {
        $gitignoreContent = Get-Content .gitignore -Raw
        if ($gitignoreContent -match "\.env") {
            Write-Host "✓ .env est dans .gitignore" -ForegroundColor Green
        } else {
            Write-Host "✗ .env n'est PAS dans .gitignore (RISQUE DE SÉCURITÉ!)" -ForegroundColor Red
            $checkStatus = 1
        }
    }
} else {
    Write-Host "⚠  .env n'existe pas (normal, à créer)" -ForegroundColor Yellow
}

Write-Host ""

# 5. Vérifier les clés en dur
Write-Host "5️⃣  Vérification des clés en dur..." -ForegroundColor Yellow
Write-Host ""

$foundKeys = $false
Get-ChildItem -Path "stripe_integration" -Filter "*.py" -Recurse | ForEach-Object {
    $content = Get-Content $_.FullName -Raw
    if ($content -match "sk_" -and $content -notmatch "os\.getenv") {
        Write-Host "✗ Clés Stripe en dur trouvées dans $($_.Name)!" -ForegroundColor Red
        $foundKeys = $true
        $checkStatus = 1
    }
}

if (-not $foundKeys) {
    Write-Host "✓ Pas de clés en dur dans le code" -ForegroundColor Green
}

Write-Host ""

# 6. Résumé
Write-Host "═════════════════════════════════════════════════════════════" -ForegroundColor Cyan
if ($checkStatus -eq 0) {
    Write-Host "✅ VÉRIFICATION RÉUSSIE!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Prochaines étapes:" -ForegroundColor Yellow
    Write-Host "1. Installer les dépendances: pip install -r requirements.txt"
    Write-Host "2. Configurer Stripe: copy .env.example .env"
    Write-Host "3. Ajouter vos clés Stripe au fichier .env"
    Write-Host "4. Exécuter les tests: pytest test\ -v"
    Write-Host ""
    Write-Host "📖 Consulter STRIPE_SETUP_GUIDE.md pour plus d'infos" -ForegroundColor Cyan
} else {
    Write-Host "❌ VÉRIFICATION ÉCHOUÉE" -ForegroundColor Red
    Write-Host "Merci de corriger les erreurs ci-dessus" -ForegroundColor Red
}
Write-Host "═════════════════════════════════════════════════════════════" -ForegroundColor Cyan

exit $checkStatus
