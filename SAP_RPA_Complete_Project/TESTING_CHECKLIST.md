# SAP RPA Testing Checklist

## Pre-Production Testing Checklist

Use this checklist before deploying the optimized code to production.

---

## ✅ Phase 1: Environment Validation

### 1.1 SAP Connection
- [ ] SAP GUI is running and accessible
- [ ] SAP connection details in `config.py` are correct
- [ ] User has proper permissions for MD04, KO03 transactions

### 1.2 Python Dependencies
```bash
cd SAP_RPA_Complete_Project
pip install -r requirements.txt
```
- [ ] All dependencies installed without errors
- [ ] Python version 3.8+ confirmed

### 1.3 Configuration Files
- [ ] `config.py` has correct field IDs for your environment
- [ ] Plant list matches your SAP system
- [ ] ERF Dashboard URL is correct (if using ERF fallback)
- [ ] VBS script paths are correct

---

## ✅ Phase 2: OrdRes Field Validation

### 2.1 Run Validation Script
```bash
python validate_ordres_fields.py
```

- [ ] Script connects to SAP successfully
- [ ] Test material with OrdRes is available
- [ ] All field IDs validate (5/5 passed)
- [ ] If any fail: Update `config.py` with correct field IDs

### 2.2 Manual Verification
Navigate to SAP manually:
1. Go to MD04
2. Enter a material with OrdRes
3. Check that the exact text in table is `'OrdRes'`
   - [ ] Text matches (not "ORDRES" or "Ord.Res")
   - [ ] If different: Update `field_manager.py` line 289

---

## ✅ Phase 3: Single Material Test

### 3.1 Test MatRes Material
Pick a material known to have MatRes:
- [ ] Material processes successfully
- [ ] Logs show: `"✓✓✓ MatRes found in plant XXXX - STOPPING search here!"`
- [ ] Data extracted correctly
- [ ] Processing time reasonable (~15-20 seconds)
- [ ] Only 1 plant checked (early termination working)

### 3.2 Test OrdRes Material
Pick a material known to have OrdRes:
- [ ] Material processes successfully
- [ ] Logs show: `"✓✓ OrdRes found in plant XXXX - Extracting data immediately!"`
- [ ] Cost center extracted
- [ ] Part description extracted
- [ ] Order number extracted
- [ ] Processing time reasonable (~20-25 seconds)
- [ ] Search stops after finding OrdRes (no STPord check)

### 3.3 Test STPord Material
Pick a material that only has STPord:
- [ ] Material processes successfully
- [ ] Logs show: `"✓ STPord found in plant XXXX - Extracting RPM immediately!"`
- [ ] RPM number extracted correctly
- [ ] ERF workflow executes (if enabled)
- [ ] Processing time reasonable (~35-45 seconds)

### 3.4 Test Material in Later Plant
Pick a material with MatRes in plant 2000 (not 1000):
- [ ] Logs show plant 1000 checked first
- [ ] Logs show MatRes found in plant 2000
- [ ] Search STOPS after plant 2000 (plants 1020, 1900 not checked)
- [ ] `'plants_checked': 2` in result

---

## ✅ Phase 4: Multi-Material Pilot

### 4.1 Prepare Test Dataset
Create Excel with 20-30 materials:
- [ ] 10 materials with MatRes
- [ ] 5 materials with OrdRes
- [ ] 5 materials with STPord
- [ ] 5 materials with nothing (will fail)

### 4.2 Run Pilot
```bash
python main.py
```

- [ ] All materials process without crashes
- [ ] Success rate matches expectations
- [ ] Check statistics in output:
  - [ ] Scenario 1 count (MatRes + OrdRes)
  - [ ] Scenario 2 count (ERF Dashboard)
  - [ ] Scenario 3 count (ERF → KO03)
  - [ ] Failures count

### 4.3 Verify Output
Check the Excel output file:
- [ ] Part_Data sheet has all processed materials
- [ ] Summary sheet shows correct statistics
- [ ] Errors sheet shows failed materials with reasons
- [ ] Data quality looks good (no blank fields where data expected)

---

## ✅ Phase 5: Performance Validation

### 5.1 Timing Checks
Monitor processing times:
- [ ] MatRes materials: Average 15-20 seconds
- [ ] OrdRes materials: Average 20-25 seconds
- [ ] STPord materials: Average 35-45 seconds
- [ ] Times are within expected ranges

### 5.2 Optimization Verification
Check logs for optimization indicators:
- [ ] `"🚀 OPTIMIZED multi-plant search"` appears
- [ ] `"STOPPING search here!"` appears when appropriate
- [ ] Plants are not checked after MatRes/OrdRes found
- [ ] No double MD04 navigation for RPM extraction

### 5.3 Early Termination Proof
Find a material with MatRes in plant 1000:
- [ ] Log shows only 1 plant checked
- [ ] `'plants_checked': 1` in result
- [ ] Total time < 20 seconds

---

## ✅ Phase 6: Error Handling

### 6.1 Test Graceful Failures
Test with invalid material:
- [ ] System logs error appropriately
- [ ] Continues to next material (doesn't crash)
- [ ] Error recorded in Errors sheet

### 6.2 Test OrdRes Extraction Failure
If possible, force OrdRes field extraction to fail:
- [ ] System logs warning
- [ ] Falls back to next plant
- [ ] Eventually tries STPord if available

### 6.3 Test Network/SAP Issues
Disconnect SAP mid-processing:
- [ ] System detects connection loss
- [ ] Error logged appropriately
- [ ] Doesn't enter infinite loop

---

## ✅ Phase 7: Integration Testing

### 7.1 Full Workflow Test
Process 5 materials through complete flow:
- [ ] MatRes → Direct extraction → Success
- [ ] OrdRes → Direct extraction → Success
- [ ] STPord → RPM extraction → ERF → Success
- [ ] STPord → RPM extraction → ERF → KO03 → Success
- [ ] No data → All scenarios → Failure

### 7.2 VBS Integration
If using VBS scripts:
- [ ] VBS scripts execute successfully
- [ ] Output parsed correctly
- [ ] Data merged with main results

### 7.3 ERF Dashboard
If using ERF fallback:
- [ ] WebDriver launches correctly
- [ ] ERF Dashboard loads
- [ ] Search executes
- [ ] Data extracted
- [ ] Browser closes cleanly

---

## ✅ Phase 8: Production Readiness

### 8.1 Documentation Review
- [ ] OPTIMIZATION_SUMMARY.md reviewed
- [ ] ORDRES_INTEGRATION.md reviewed
- [ ] Team understands new 3-tier priority system

### 8.2 Backup Plan
- [ ] Current production code backed up
- [ ] Know how to revert if needed
- [ ] Legacy methods still available if optimization causes issues

### 8.3 Monitoring Setup
- [ ] Log files directory writable
- [ ] Log rotation configured (if needed)
- [ ] Know where to check logs during production run

### 8.4 Performance Baseline
Document current performance for comparison:
- [ ] Average time per material: ______ seconds
- [ ] Success rate: ______%
- [ ] Average plants checked: ______

---

## ✅ Phase 9: Production Deployment

### 9.1 Gradual Rollout
- [ ] Day 1: Process 50 materials, monitor closely
- [ ] Day 2: Process 100 materials if Day 1 successful
- [ ] Day 3: Process 200 materials if Day 2 successful
- [ ] Week 2: Full production deployment

### 9.2 Monitor During Rollout
Watch for these indicators:
- [ ] Processing time reduced (20-40% faster)
- [ ] Success rate maintained or improved
- [ ] Average plants checked < 2
- [ ] No crashes or infinite loops
- [ ] OrdRes materials processing successfully

### 9.3 Collect Metrics
After production run, document:
- Total materials: ______
- Scenario 1 (MatRes + OrdRes): ______
- Scenario 2 (ERF): ______
- Scenario 3 (ERF→KO03): ______
- Failures: ______
- Success rate: ______%
- Average time per material: ______ seconds
- Time savings vs previous: ______%

---

## 🚨 Rollback Criteria

Stop and rollback if:
- [ ] Success rate drops > 10%
- [ ] System crashes repeatedly
- [ ] Processing time increases instead of decreasing
- [ ] OrdRes extraction fails > 80% of the time
- [ ] Data quality issues detected

---

## 📞 Support Contacts

If issues arise:
1. Check logs in `SAP_RPA_Complete_Project/logs/`
2. Review TROUBLESHOOTING.md
3. Contact: [Your support contact]

---

## ✅ Sign-Off

Testing completed by: _________________
Date: _________________
Production deployment approved: Yes / No

Notes:
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________
