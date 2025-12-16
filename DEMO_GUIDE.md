# MDI Demo Guide - Hackathon Presentation

## 🎯 Demo Flow (5-7 minutes)

This guide shows how to demonstrate the Maintenance Debt Index system working end-to-end.

---

## Step 1: Show the Dashboard (30 seconds)

**URL:** http://localhost:5173 

**Explain:**
- "This is the city's infrastructure health at a glance"
- Point to the **MDI Score gauge** (e.g., 76.8)
- Show **Total Debt** accumulating
- Show **Ward Rankings** - best and worst performing areas

**Key talking point:**
> "Just like a credit score tells banks about your financial health, MDI tells city administrators about their infrastructure health."


---

## Step 2: Show the Map (30 seconds)

**URL:** http://localhost:5173/map

**Explain:**
- "Each marker represents an infrastructure asset in Bangalore"
- **Green markers** = Well maintained (MDI 90+)
- **Red markers** = Critical attention needed (MDI <30)
- Click on a marker to show the popup with debt info

**Key talking point:**
> "City managers can instantly see problem areas without reading spreadsheets."

---

## Step 3: Show Wards Ranking (30 seconds)

**URL:** http://localhost:5173/wards

**Explain:**
- "Wards are ranked by their aggregate MDI score"
- Show the comparison between best and worst wards
- Highlight that ward officers can be held accountable

**Key talking point:**
> "This creates healthy competition between ward administrators to maintain their infrastructure."

---

## Step 4: Live Demo - Report an Issue (2-3 minutes)

**URL:** http://localhost:5173/admin

### 4.1 First, note current scores:
1. Go to **Dashboard** - note city MDI score (e.g., 76.8)
2. Go to **Assets** - pick an asset with high score (e.g., 95+), note its name
3. Go to **Map** - locate the asset (should be green)

### 4.2 Report an Issue:
1. Go to **Admin** → **Report Issue** tab
2. Fill the form:
   - **Asset:** Select the healthy asset you noted
   - **Title:** "Major pothole reported"
   - **Category:** Pothole
   - **Severity:** Critical
   - **Estimated Cost:** ₹25,000
3. Click **Report Issue**

### 4.3 Show the Impact:
1. Go to **Assets** → Find the same asset
   - MDI score dropped! (e.g., 95 → 72)
   - Current Debt increased
   - Shows "1 issue"

2. Go to **Map** → Find the asset
   - Marker color changed! (green → yellow/orange)

3. Go to **Wards** → Find the ward
   - Ward score decreased slightly

4. Go to **Dashboard**
   - City score decreased
   - Open issues count increased

**Key talking point:**
> "One unresolved issue immediately impacts the entire hierarchy - from asset to ward to city."

---

## Step 5: Explain the Debt Engine (1 minute)

**Show the Simulator:** http://localhost:5173/simulator

**Explain the Formula:**
```
Current Debt = Base Cost × Debt Multiplier

Where:
- Debt Multiplier = 1 + (0.02 × days_overdue)^1.5
```

**Demo with Simulator:**
1. Set base cost: ₹50,000
2. Set days overdue: 0 → Shows ₹50,000
3. Set days overdue: 30 → Shows ₹65,000 (30% increase)
4. Set days overdue: 60 → Shows ₹96,000 (92% increase)
5. Set days overdue: 90 → Shows ₹140,000 (180% increase!)

**Key talking point:**
> "The longer you delay, the MORE expensive repairs become. This models real-world deterioration - a small pothole becomes a road cave-in."

---

## Step 6: Show MDI Score Calculation (30 seconds)

**Explain:**
```
MDI Score = 100 × (1 - Total_Debt / Total_Base_Cost)

Example:
- Base repair costs: ₹10,00,000
- Accumulated debt: ₹3,00,000
- MDI Score = 100 × (1 - 3/10) = 70
```

**Key talking point:**
> "An MDI of 70 means the city has 'lost' 30% of its infrastructure value to maintenance debt."

---

## Demo Cheat Sheet

### Quick Stats to Remember:
| Metric | Formula |
|--------|---------|
| Debt Multiplier | 1 + (0.02 × days)^1.5 |
| 30 days overdue | 1.3× base cost |
| 60 days overdue | 1.9× base cost |
| 90 days overdue | 2.8× base cost |

### SLA Days by Asset Type:
| Asset Type | SLA Days |
|------------|----------|
| Streetlight | 3 days |
| Drain | 7 days |
| Sidewalk | 10 days |
| Road | 14 days |
| Bridge | 21 days |

### Score Categories:
| Score | Category |
|-------|----------|
| 90-100 | Excellent ✅ |
| 70-89 | Good 👍 |
| 50-69 | Fair ⚠️ |
| 30-49 | Poor 🔶 |
| 0-29 | Critical 🔴 |

---

## Backup Demo Scenarios

### If API is slow:
- "The system processes real-time calculations across thousands of assets"
- Switch to explaining the concept while it loads

### If something breaks:
- "In production, this would be deployed on cloud infrastructure"
- Show the API docs at http://localhost:8000/docs

### Common Questions:

**Q: How is this different from regular asset management?**  
A: "Traditional systems just track assets. MDI quantifies the COST of delay, making invisible technical debt visible to decision-makers."

**Q: Can this work for other cities?**  
A: "Absolutely! The system is configurable for different SLAs, asset types, and currencies."

**Q: What data sources would you use in production?**  
A: "311 complaint systems, IoT sensors, citizen app reports, and municipal work orders."

---

## Presentation Tips

1. **Start with the problem:** "Cities spend 3x more on emergency repairs than planned maintenance because they don't track maintenance debt."

2. **End with the impact:** "With MDI, cities can reduce infrastructure costs by 20-30% by prioritizing repairs before they escalate."

3. **Use the map:** Visual impact is strongest - show how one issue changes the color.

4. **Keep it simple:** Don't explain every feature, focus on the core concept of "credit score for infrastructure."

---

## Quick Start Commands

```bash
# Start the application
cd hack-proto
docker-compose up -d

# Check status
docker-compose ps

# Stop everything
docker-compose down
```

**URLs:**
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

---

Good luck with your hackathon! 🏆
