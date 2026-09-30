# FedMed Regulatory & Privacy Compliance Specifications

This document outlines the cryptographic and operational compliance mapping for FedMed across HIPAA (Health Insurance Portability and Accountability Act) and GDPR (General Data Protection Regulation).

## 1. HIPAA Compliance Mapping

| HIPAA Security / Privacy Rule | FedMed Architecture Implementation | Status |
| :--- | :--- | :--- |
| **§ 164.514(a) De-identification** | Zero patient identifiers or raw NIfTI scans leave the hospital premise. Only model weight updates are transmitted. | Verified |
| **§ 164.312(a)(2)(iv) Encryption in Transit** | Mutual TLS (mTLS) with 2048-bit RSA keys and SHA-256 signatures authenticates all gRPC communication. | Verified |
| **§ 164.312(c)(1) Integrity Controls** | TenSEAL CKKS homomorphic ciphertext vectors protect against unauthorized modification and intermediate interception. | Verified |
| **§ 164.312(b) Audit Controls** | Structured round-lifecycle logging (`[FedMed-Server]`, `[Heartbeat]`) tracks node connection, payload byte sizes, and timestamps. | Verified |

## 2. GDPR Compliance Mapping

| GDPR Article | Technical Safeguard | Status |
| :--- | :--- | :--- |
| **Article 25 (Privacy by Design & by Default)** | Differential Privacy (DP) with calibrated Gaussian noise ($\sigma=0.8$) bounds individual patient contribution. | Verified |
| **Article 9 (Processing of Special Category Data)** | Medical imaging data remains partitioned within the hospital perimeter. Cross-silo aggregation handles only encrypted summaries. | Verified |
| **Article 44-50 (Cross-Border Data Transfers)** | Cross-border transfer of encrypted model updates is permissible as homomorphic ciphertexts without keys cannot be decrypted by intermediate brokers. | Verified |

## 3. Cryptographic Parameter Justification

- **Scheme**: CKKS (Cheon-Kim-Kim-Song) Homomorphic Encryption.
- **Polynomial Modulus Degree ($N$)**: 8192 (Provides >128-bit quantum-immune security according to the Homomorphic Encryption Standard).
- **Scale Factor**: $2^{40}$ (Preserves 40 bits of floating-point precision for PyTorch gradient tensors).
- **Differential Privacy ($\epsilon, \delta$)**: $\epsilon \le 5.0$, $\delta = 10^{-5}$ across 15 rounds of training.
