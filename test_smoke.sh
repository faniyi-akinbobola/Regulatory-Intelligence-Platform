#!/bin/bash
# Parallel smoke tests — all 5 submitted at once, polled concurrently
# Finishes in ~100s regardless of test count
# Usage: bash test_smoke.sh

BASE="http://localhost:8000"
POLL_INTERVAL=6
MAX_WAIT=180
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'

echo -e "${YELLOW}Parallel smoke tests — $BASE${NC}"
echo ""

# ── Health check ──────────────────────────────────────────────────────────
echo -n "Health check... "
health=$(curl -s "$BASE/health")
pg=$(echo "$health" | python3 -c "import json,sys; print(json.load(sys.stdin)['services']['postgres'])" 2>/dev/null)
qd=$(echo "$health" | python3 -c "import json,sys; print(json.load(sys.stdin)['services']['qdrant'])" 2>/dev/null)
if [ "$pg" = "connected" ] && [ "$qd" = "connected" ]; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}UNHEALTHY — postgres=$pg qdrant=$qd — is the server running?${NC}"
    exit 1
fi
echo ""

# ── Test definitions ──────────────────────────────────────────────────────
NAMES=(
    "Investment platform — shares & bonds (expect SEC)"
    "Microfinance bank deposit insurance (expect NDIC)"
    "Payment processor tax obligations (expect FIRS/NRS)"
    "Digital wallet AML/KYC obligations (expect CBN)"
    "PSB with savings + interest (expect CBN, structural conflict)"
)
PAYLOADS=(
    '{"business_description":"I want to launch an investment platform that allows retail investors to buy shares and bonds in Nigerian companies.","business_sector":"fintech"}'
    '{"business_description":"We are a licensed microfinance bank and want to understand our deposit insurance obligations and what premiums we must pay to the deposit insurer.","business_sector":"banking"}'
    '{"business_description":"We process payments for merchants across Nigeria and need to understand tax withholding, VAT remittance, and stamp duty obligations.","business_sector":"payments"}'
    '{"business_description":"We are building a digital wallet product and need to understand AML, KYC, transaction monitoring and suspicious activity reporting obligations.","business_sector":"fintech"}'
    '{"business_description":"We want to launch a Payment Service Bank that accepts deposits from customers and pays interest on their savings balance.","business_sector":"fintech"}'
)
EXPECT=("SEC" "NDIC" "FIRS" "CBN" "CBN")

# ── Submit all 5 simultaneously ───────────────────────────────────────────
declare -a RIDS
echo "Submitting all 5 analyses simultaneously..."
for i in 0 1 2 3 4; do
    resp=$(curl -s -X POST "$BASE/analyze/analyze-business" \
        -H "Content-Type: application/json" \
        -d "${PAYLOADS[$i]}")
    rid=$(echo "$resp" | python3 -c "import json,sys; print(json.load(sys.stdin).get('report_id','ERROR'))" 2>/dev/null)
    RIDS[$i]="$rid"
    echo "  Test $((i+1)): $rid"
done
echo ""

# ── Poll all until every one is done ─────────────────────────────────────
declare -a DONE=(false false false false false)
declare -a RESPS
waited=0
echo "Polling..."
while true; do
    sleep $POLL_INTERVAL
    waited=$((waited + POLL_INTERVAL))
    pending=0
    for i in 0 1 2 3 4; do
        if [ "${DONE[$i]}" = "false" ]; then
            r=$(curl -s "$BASE/analyze/report/${RIDS[$i]}")
            st=$(echo "$r" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status','?'))" 2>/dev/null)
            if [ "$st" = "completed" ] || [ "$st" = "failed" ]; then
                DONE[$i]="true"
                RESPS[$i]="$r"
                echo -e "  [${waited}s] Test $((i+1)) — ${st}"
            else
                pending=$((pending+1))
            fi
        fi
    done
    [ $pending -eq 0 ] && break
    [ $waited -ge $MAX_WAIT ] && { echo -e "${RED}Timeout${NC}"; break; }
    echo "  [${waited}s] $pending still running..."
done

# ── Print results ─────────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════════════════════════════"
PASS=0; FAIL=0
for i in 0 1 2 3 4; do
    echo ""
    echo -e "${YELLOW}TEST $((i+1)): ${NAMES[$i]}${NC}"
    echo "────────────────────────────────────────────────────────────────"

    resp="${RESPS[$i]}"
    if [ -z "$resp" ]; then
        echo -e "${RED}✗ TIMEOUT${NC}"; FAIL=$((FAIL+1)); continue
    fi

    st=$(echo "$resp" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status'))" 2>/dev/null)
    if [ "$st" = "failed" ]; then
        err=$(echo "$resp" | python3 -c "import json,sys; print(json.load(sys.stdin).get('error','?'))" 2>/dev/null)
        echo -e "${RED}✗ WORKFLOW FAILED — $err${NC}"; FAIL=$((FAIL+1)); continue
    fi

    echo "$resp" | python3 -c "
import json, sys
d = json.load(sys.stdin)
r = d.get('report') or {}
print('AUDIT_ID   :', d.get('audit_id','none'))
print('RISK       :', r.get('risk_level','?'), '(score:', str(r.get('risk_score','?')) + ')')
print('OBLIGATIONS:', len(r.get('obligations',[])), ' GAPS:', len(r.get('compliance_gaps',[])), ' CHECKLIST:', len(r.get('compliance_checklist',[])))
print()
print('REGULATORS CITED:')
seen = {}
for c in r.get('citations', []):
    reg = c.get('regulator','UNKNOWN')
    doc = c.get('document','?')[:55]
    if reg not in seen: seen[reg] = doc
for reg, doc in seen.items():
    print(f'  [{reg}]  {doc}')
" 2>/dev/null

    found=$(echo "$resp" | python3 -c "
import json,sys
d=json.load(sys.stdin); r=d.get('report') or {}
print('|'.join(set(c.get('regulator','') for c in r.get('citations',[]))))
" 2>/dev/null)

    expect="${EXPECT[$i]}"
    if echo "$found" | grep -qi "$expect"; then
        echo -e "\n${GREEN}✓ PASS — '$expect' found in: $found${NC}"
        PASS=$((PASS+1))
    else
        echo -e "\n${RED}✗ FAIL — '$expect' NOT found. Got: $found${NC}"
        FAIL=$((FAIL+1))
    fi
done

echo ""
echo "════════════════════════════════════════════════════════════════"
if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}ALL $PASS/5 TESTS PASSED — backend is ready for the UI${NC}"
else
    echo -e "${GREEN}$PASS passed${NC}  ${RED}$FAIL failed${NC} out of 5"
fi
echo "════════════════════════════════════════════════════════════════"


GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

run_test() {
    local name="$1"
    local payload="$2"
    local expect_regulator="$3"  # partial string to check in regulator list

    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo -e "${YELLOW}TEST: $name${NC}"
    echo "Expecting regulator: $expect_regulator"
    echo "═══════════════════════════════════════════════════════"

    # Step 1: Submit
    local resp=$(curl -s -X POST "$BASE/analyze/analyze-business" \
        -H "Content-Type: application/json" \
        -d "$payload")

    local report_id=$(echo "$resp" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('report_id','ERROR'))" 2>/dev/null)

    if [ "$report_id" = "ERROR" ] || [ -z "$report_id" ]; then
        echo -e "${RED}✗ FAILED — could not submit request. Response: $resp${NC}"
        FAIL=$((FAIL + 1))
        return
    fi
    echo "→ report_id: $report_id"

    # Step 2: Poll until complete
    local waited=0
    local final_resp=""
    while [ $waited -lt $MAX_WAIT ]; do
        sleep $POLL_INTERVAL
        waited=$((waited + POLL_INTERVAL))
        local status_resp=$(curl -s "$BASE/analyze/report/$report_id")
        local st=$(echo "$status_resp" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status','unknown'))" 2>/dev/null)
        echo "  [${waited}s] status: $st"
        if [ "$st" = "completed" ] || [ "$st" = "failed" ]; then
            final_resp="$status_resp"
            break
        fi
    done

    if [ -z "$final_resp" ]; then
        echo -e "${RED}✗ FAILED — timed out after ${MAX_WAIT}s${NC}"
        FAIL=$((FAIL + 1))
        return
    fi

    # Step 3: Parse and report
    echo ""
    echo "$final_resp" | python3 -c "
import json, sys

d = json.load(sys.stdin)
status = d.get('status')
error = d.get('error')
report = d.get('report') or {}

if status == 'failed':
    print('STATUS: FAILED — ' + str(error))
    sys.exit(1)

print('AUDIT_ID :', d.get('audit_id'))
print('RISK     :', report.get('risk_level'), '(score:', str(report.get('risk_score', '?')) + ')')
print('EXEC SUMMARY:', (report.get('executive_summary') or '')[:120] + '...')
print()
print('REGULATORS CITED:')
seen = {}
for c in report.get('citations', []):
    r = c.get('regulator', '?')
    doc = c.get('document', '?')
    if r not in seen:
        seen[r] = []
    seen[r].append(doc[:60])
for reg, docs in seen.items():
    print(f'  [{reg}]')
    for d2 in docs:
        print(f'    - {d2}')

print()
print('OBLIGATIONS:', len(report.get('obligations', [])))
print('GAPS       :', len(report.get('compliance_gaps', [])))
print('CHECKLIST  :', len(report.get('compliance_checklist', [])))
"

    # Step 4: Check expected regulator
    local found=$(echo "$final_resp" | python3 -c "
import json, sys
d = json.load(sys.stdin)
report = d.get('report') or {}
regs = set(c.get('regulator','') for c in report.get('citations', []))
print(' | '.join(regs))
" 2>/dev/null)

    if echo "$found" | grep -qi "$expect_regulator"; then
        echo -e "${GREEN}✓ PASS — '$expect_regulator' found in regulators: $found${NC}"
        PASS=$((PASS + 1))
    else
        echo -e "${RED}✗ FAIL — '$expect_regulator' NOT found. Got: $found${NC}"
        FAIL=$((FAIL + 1))
    fi
}

echo "Starting smoke tests against $BASE"
echo "Server health check..."
health=$(curl -s "$BASE/health")
echo "$health" | python3 -m json.tool 2>/dev/null || echo "$health"
echo ""

# Test 1 — ISA 2025 → SEC Nigeria (not CBN)
run_test \
    "Investment platform — shares & bonds (expect SEC)" \
    '{"business_description": "I want to launch an investment platform that allows retail investors to buy shares and bonds in Nigerian companies.", "business_sector": "fintech"}' \
    "SEC"

# Test 2 — Deposit insurance → NDIC
run_test \
    "Microfinance bank deposit insurance (expect NDIC)" \
    '{"business_description": "We are a licensed microfinance bank and want to understand our deposit insurance obligations and what premiums we must pay to the deposit insurer.", "business_sector": "banking"}' \
    "NDIC"

# Test 3 — Tax withholding → FIRS
run_test \
    "Payment processor tax obligations (expect FIRS or NRS)" \
    '{"business_description": "We process payments for merchants across Nigeria and need to understand our tax withholding, VAT remittance, and stamp duty obligations.", "business_sector": "payments"}' \
    "FIRS"

# Test 4 — AML/KYC → CBN + EFCC
run_test \
    "Digital wallet AML and KYC obligations (expect CBN or EFCC)" \
    '{"business_description": "We are building a digital wallet product and need to understand AML, KYC, transaction monitoring and suspicious activity reporting obligations.", "business_sector": "fintech"}' \
    "CBN"

# Test 5 — PSB structural conflict (interest on balance is prohibited for PSB)
run_test \
    "PSB wallet with savings and interest (expect CBN + structural conflict)" \
    '{"business_description": "We want to launch a Payment Service Bank that accepts deposits from customers and pays interest on their savings balance.", "business_sector": "fintech"}' \
    "CBN"

echo ""
echo "═══════════════════════════════════════════════════════"
echo -e "RESULTS: ${GREEN}$PASS passed${NC}  ${RED}$FAIL failed${NC}"
echo "═══════════════════════════════════════════════════════"
