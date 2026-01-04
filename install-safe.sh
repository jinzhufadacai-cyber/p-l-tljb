#!/bin/bash
# Safe installation script for Lighter-Paradex arbitrage bot
# This script avoids pulling in torch and other heavy ML dependencies
# Usage: bash install-safe.sh

set -e  # Exit on error

echo "=========================================="
echo "Safe Installation for Arbitrage Bot"
echo "=========================================="

# Check Python version
echo "Checking Python version..."
python3 --version || { echo "Python3 not found"; exit 1; }

# Create virtual environment (optional)
read -p "Create virtual environment? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "Virtual environment activated"
fi

# Method 1: Use requirements-safe.txt (recommended)
echo "Method 1: Installing using requirements-safe.txt..."
echo "This uses starknet-py==0.20.0 to avoid torch dependencies"
pip install -r requirements-safe.txt

# Verify installation
echo "Verifying installation..."
python3 -c "
try:
    import lighter
    print('✅ lighter imported successfully')
except ImportError as e:
    print(f'❌ lighter import failed: {e}')

try:
    import paradex_py
    print('✅ paradex_py imported successfully')
except ImportError as e:
    print(f'❌ paradex_py import failed: {e}')

try:
    import starknet_py
    print('✅ starknet_py imported successfully')
except ImportError as e:
    print(f'⚠️ starknet_py import failed (may not affect core functionality): {e}')
"

# Method 2: Alternative using constraints (if Method 1 fails)
read -p "Did Method 1 succeed? If not, try Method 2 with constraints? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Method 2: Installing with constraints to exclude torch..."
    pip install -r requirements.txt -c constraints.txt
fi

# Method 3: Step-by-step installation (most control)
read -p "Try step-by-step installation for maximum control? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Method 3: Step-by-step installation..."
    
    echo "Step 1: Installing core dependencies..."
    pip install python-telegram-bot>=20.7 aiohttp>=3.8.0 websockets>=12.0 \
                python-dotenv>=1.0.0 requests>=2.31.0 cryptography>=42.0.0
    
    echo "Step 2: Installing blockchain SDKs..."
    pip install web3>=6.0.0 ccxt>=4.3.0
    
    echo "Step 3: Installing lighter..."
    pip install lighter>=0.1.0
    
    echo "Step 4: Installing paradex-py..."
    pip install git+https://github.com/tradeparadex/paradex-py.git@7eb7aa3825d466b2f14abd3e94f2ce6b002d6a63
    
    echo "Step 5: Installing starknet-py WITHOUT dependencies..."
    pip install starknet-py==0.20.0 --no-deps
    echo "Installing starknet-py core dependencies manually..."
    pip install marshmallow>=3.20.0 dataclasses-json>=0.5.0 typing-extensions>=4.0.0
fi

# Final verification
echo "=========================================="
echo "Final verification..."
echo "=========================================="

# Check if torch was accidentally installed
if pip list | grep -i torch; then
    echo "⚠️  Warning: torch was installed. You may want to remove it:"
    echo "   pip uninstall torch torchvision torchaudio triton -y"
else
    echo "✅ Good: torch is not installed"
fi

# Run the test script
echo "Running test script..."
if [ -f test_real_exchanges.py ]; then
    python3 test_real_exchanges.py --check-only || echo "Test script had issues, but installation may still work"
else
    echo "Test script not found"
fi

echo "=========================================="
echo "Installation complete!"
echo "Next steps:"
echo "1. Configure your .env file with API keys"
echo "2. Run: python3 test_real_exchanges.py"
echo "3. Start the bot: python3 main.py"
echo "=========================================="