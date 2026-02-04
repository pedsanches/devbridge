#!/bin/bash
# Governance Script: lint-ui.sh
# Purpose: Detect hardcoded values in UI components

EXIT_CODE=0

echo "🔍 Scanning for UI Governance violations..."

# 1. Detect Hex colors (e.g., #FFFFFF) in TSX/JSX
if grep -rE "#[0-9a-fA-F]{3,6}" frontend/src/components --include=*.tsx --include=*.jsx --exclude=*.spec.tsx; then
  echo "❌ Error: Hardcoded HEX colors detected in components."
  echo "👉 Use tokens from foundations.md (e.g., var(--color-primary))"
  EXIT_CODE=1
fi

# 2. Detect Arbitrary Tailwind values (e.g., bg-[#...], p-[15px])
if grep -rE "\[#[0-9a-fA-F]+\]|\[[0-9]+px\]" frontend/src/components --include=*.tsx; then
  echo "❌ Error: Arbitrary Tailwind values detected."
  echo "👉 Use standard Tailwind classes mapped to tokens (e.g., p-4, bg-primary)"
  EXIT_CODE=1
fi

# 3. Detect hardcoded pixels in style props
if grep -rE "style=\{\{.*[0-9]+px.*\}\}" frontend/src/components --include=*.tsx; then
    echo "❌ Error: Hardcoded pixels in style prop."
    EXIT_CODE=1
fi

if [ $EXIT_CODE -eq 0 ]; then
  echo "✅ UI Governance Check Passed: No hardcoded values found."
else
  echo "⚠️ Governance Failed. Please fix the above violations."
fi

exit $EXIT_CODE
