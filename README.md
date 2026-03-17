# Automated Customer Health Monitoring System

## Overview
This project is a Python-based automation system designed to analyze customer lead performance, combine it with operational audit data, and generate standardized health check reports at scale.

The system processes lead report data, validates website CTA presence using screenshot matching, and produces PDF reports that highlight performance trends and potential risks.

---

## Business Impact

This system simulates a real-world operational workflow used in customer success and digital performance monitoring.

By automating the analysis of lead performance and website CTA presence, the system helps:

- Identify underperforming accounts
- Detect missing or broken conversion paths
- Standardize reporting across multiple customers
- Reduce manual audit and reporting effort

This type of automation enables teams to proactively manage customer health and improve conversion outcomes at scale.

## Key Features

- Automated processing of lead report datasets
- Customer health analysis using Q2 vs Q3 lead performance
- Screenshot-based CTA validation (SRP prioritized over VDP)
- Detection of missing ESHOP CTAs
- Dealer code normalization (e.g., 08564 → 8564)
- Automated PDF report generation
- Scalable workflow tested across 135+ datasets

---

## Project Structure
├── Document_Generator/
│ ├── main.py
│ ├── data_loader.py
│ ├── doc_output.py
│ ├── email_generator.py
│ └── lead_metrics_loader.py
├── demo_dataset/
│ ├── button_stack_screenshots/
│ ├── lead_reports/
│ └── Master_Health_Check_Data.csv
├── Health_Checks/
│ └── sample output PDFs
├── requirements.txt
└── README.md

---

## How It Works

1. Loads dealer audit data from master CSV
2. Processes individual lead report files
3. Matches screenshots using dealer code prefix
4. Prioritizes SRP CTA screenshots over VDP
5. Identifies missing CTA implementations
6. Generates structured PDF health reports

---

## Sample Use Case

The system was validated across 135 dealer datasets and is demonstrated here using a curated sample set to showcase:

- Performance growth detection
- Performance decline detection
- Missing CTA identification
- Data normalization handling
- Screenshot-based validation logic

---

## Results

- Processed 135+ dealer-level datasets
- Generated 135 automated health-check reports
- Achieved 0 processing failures in validation runs
- Successfully handled:
  - Missing CTA detection
  - Data normalization inconsistencies
  - Screenshot prioritization logic

## Installation

```bash
pip install -r requirements.txt

Run the Project
python Document_Generator/main.py
Technologies Used

Python

ReportLab (PDF generation)

CSV Data Processing

Workflow Automation

Operational Analytics

Author

Doc Pulliam
