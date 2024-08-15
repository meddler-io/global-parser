# **DefectDojo Parser - Stateless Container**

A mirror of the popular DefectDojo project with added functionality for stateless containerization. This lightweight container provides a one-time report parsing mechanism that converts vulnerability scan outputs into standardized JSON/JSONL formats, easily ingestible into your SIEM, Elasticsearch, MongoDB, or other security data platforms.

## **Why This Project?**

Organizations today rely on a variety of open-source tools for security and vulnerability scanning, each with their own evolving report formats. Aggregating this data into a unified format is often cumbersome and time-consuming.

While DefectDojo excels at parsing and normalizing reports from numerous tools, not everyone wants to fully migrate to its UI, terminology, or its complete ecosystem. This project offers a flexible, headless alternative that integrates seamlessly into CI/CD and DevSecOps pipelines.

### **Features**

- **Stateless Container**: Runs as a one-time container that accepts reports, parses them, and outputs standardized JSON/JSONL files for ingestion.
- **Integration Flexibility**: Supports ingesting into your SIEM, Elasticsearch, MongoDB, and other platforms that rely on structured data.
- **Tool Agnostic**: Works with a wide range of open-source vulnerability scanners thanks to DefectDojo's constantly updated parsers.
- **CI/CD Ready**: Built to be easily integrated into your CI/CD pipeline for automated report parsing.
- **No UI/Terminology Overhaul**: Avoids forcing users to adapt to new UIs or security terminologies—just parse and output.

## **Use Case**

This tool is ideal for organizations that:
- Use multiple vulnerability scanners or open-source security tools.
- Want a quick, standardized parsing solution without migrating to a complete platform like DefectDojo.
- Need a flexible, automated way to aggregate and normalize data from various sources.
- Seek a lightweight, stateless container for DevSecOps pipelines.

## **Getting Started**

### **Prerequisites**

- Docker installed on your machine.
- Vulnerability reports generated from supported tools.

### **How to Use**

1. **Clone the Repository**

    ```bash
    git clone https://github.com/meddler-io/global-parser.git
    cd global-parser
    ```

2. **Build the Docker Image**

    ```bash
    docker build -t global-parser .
    ```

3. **Run the Container**

    ```bash
    docker run --rm -v /path/to/reports:/reports -v /path/to/output:/output global-parser --parser_id=='Checkmarx Scan' --report_file='/reports/sample_checkmarx_report.xml' --result_file='/output/formatted.jsonl'
    ```


4. **Output**

    The container will parse the reports and generate the normalized JSON/JSONL files in the specified output directory.

### **Example**

```bash
docker run --rm -v /path/to/reports:/reports -v /path/to/output:/output global-parser --parser_id=='Checkmarx Scan' --report_file='/reports/sample_checkmarx_report.xml' --result_file='/output/formatted.jsonl'
```
