#!/bin/bash
# Example script to compare Python versions
#
# This script demonstrates how to benchmark multiple Python versions
# and compare the results to understand performance improvements.

set -e

echo "=================================="
echo "Python Version Comparison Script"
echo "=================================="
echo ""

# Check if pyenv is available
if ! command -v pyenv &> /dev/null; then
    echo "⚠️  pyenv not found. Install with:"
    echo "   curl https://pyenv.run | bash"
    echo ""
    echo "Or manually create virtual environments for each Python version."
    exit 1
fi

# Python versions to test (customize as needed)
VERSIONS=("3.11.8" "3.12.3" "3.13.0")
RESULTS_DIR="comparison_results"

mkdir -p "$RESULTS_DIR"

echo "Testing Python versions: ${VERSIONS[*]}"
echo ""

# Install Python versions if needed
for version in "${VERSIONS[@]}"; do
    if ! pyenv versions --bare | grep -q "^${version}$"; then
        echo "Installing Python ${version}..."
        pyenv install "$version"
    fi
done

# Run benchmarks for each version
for version in "${VERSIONS[@]}"; do
    echo ""
    echo "========================================"
    echo "Benchmarking Python ${version}"
    echo "========================================"
    echo ""

    # Create/activate virtual environment
    VENV_DIR="venv_${version//./_}"

    if [ ! -d "$VENV_DIR" ]; then
        echo "Creating virtual environment for Python ${version}..."
        pyenv local "$version"
        python -m venv "$VENV_DIR"
    fi

    # Activate and install dependencies
    source "${VENV_DIR}/bin/activate"

    echo "Installing dependencies..."
    pip install -q --upgrade pip
    pip install -q pytest pytest-benchmark numpy

    # Try to install PyTorch (may fail on some platforms)
    pip install -q torch 2>/dev/null || echo "⚠️  PyTorch install failed, skipping PyTorch benchmarks"

    # Run benchmarks
    echo "Running benchmarks..."
    RESULT_FILE="${RESULTS_DIR}/results_${version//./_}.json"

    python benchmarks/run_benchmarks.py \
        --output-dir "$RESULTS_DIR" \
        --categories numpy async memory startup

    # Rename the generated file for consistency
    LATEST=$(ls -t "${RESULTS_DIR}"/benchmarks_*.json | head -1)
    mv "$LATEST" "$RESULT_FILE"

    echo "✅ Results saved to: ${RESULT_FILE}"

    deactivate
done

# Compare results
echo ""
echo "========================================"
echo "Comparing Results"
echo "========================================"
echo ""

RESULT_FILES=()
for version in "${VERSIONS[@]}"; do
    RESULT_FILES+=("${RESULTS_DIR}/results_${version//./_}.json")
done

# Use first version as baseline
BASELINE="${RESULT_FILES[0]}"
COMPARISONS=("${RESULT_FILES[@]:1}")

python benchmarks/utils/compare_results.py "$BASELINE" "${COMPARISONS[@]}"

echo ""
echo "✨ Comparison complete!"
echo ""
echo "Results saved in: ${RESULTS_DIR}/"
