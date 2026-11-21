# HỆ THỐNG TRUY XUẤT NGUỒN GỐC CHUỖI CUNG ỨNG TÔM NUÔI

## 1. Giới thiệu

Đề tài nghiên cứu ứng dụng Blockchain kết hợp Ontology trong truy xuất nguồn gốc chuỗi cung ứng tôm nuôi.

Chuỗi sự kiện nghiệp vụ:

SEED_STOCKING -> FEEDING -> TREATMENT -> HARVEST -> PROCESSING -> SHIPPING -> DISTRIBUTION

Blockchain được sử dụng để bảo đảm tính toàn vẹn dữ liệu sự kiện. Ontology hỗ trợ biểu diễn ngữ nghĩa, suy luận và truy vấn dữ liệu truy xuất nguồn gốc.

## 2. Môi trường và công nghệ

- Python 3.14.7
- Hyperledger Fabric 2.5.16
- Node.js 18.20.8
- npm 10.8.2
- RDF/OWL và RDFLib
- SWRL
- SHACL / pySHACL
- SPARQL
- Flask
- QR Code
- YAML

## 3. Cấu trúc project

- 02_preprocessed/mapped/hashed_events: 116 sự kiện đã tạo hash.
- 02_preprocessed/mapped/payloads: 116 payload off-chain.
- 03_ontology/owl: các phiên bản ontology.
- 03_ontology/shacl: SHACL Shapes.
- 03_ontology/sparql: truy vấn SPARQL.
- 03_ontology/results: kết quả thực nghiệm ontology.
- 04_blockchain/fabric_network: cấu hình mạng và mã nguồn chaincode Hyperledger Fabric.
- 04_blockchain/results: metadata, ledger events và kết quả thực nghiệm blockchain.
- 05_demo/qr_codes: QR truy xuất.
- 05_demo/qr_urls: QR truy cập giao diện Web.
- 05_demo/web: ứng dụng Flask.
- generated_events: dữ liệu CSV đầu vào.
- src: mã nguồn xử lý, mapping, kiểm chứng và thực nghiệm.
- tests: unit tests.

## 4. Cài đặt thư viện Python

Tại thư mục gốc project:

    python -m pip install -r requirements.txt

## 5. Cấu hình

Cấu hình chính nằm trong:

    config.yaml

Các chương trình Python sử dụng file cấu hình để xác định đường dẫn dữ liệu và các thành phần của hệ thống.

## 6. Ontology

Các file chính:

    03_ontology/owl/ontology_backup_before_merge.owl
    03_ontology/owl/ontology_2_mapped_events.owl
    03_ontology/owl/ontology_3_blockchain_enriched.owl

Ontology cuối cùng chứa 116 TraceabilityEvent.

Hệ thống sử dụng SWRL cho luật suy luận, SHACL để kiểm tra ràng buộc và SPARQL để truy vấn dữ liệu truy xuất nguồn gốc.

## 7. Blockchain

Mạng Hyperledger Fabric thử nghiệm gồm ba tổ chức nghiệp vụ:

- FarmOrg / FarmMSP
- ProcessingOrg / ProcessingMSP
- DistributionOrg / DistributionMSP

Channel:

    traceabilitychannel

Chaincode:

    traceability

Chaincode version 1.0, sequence 1.

Source Fabric:

    04_blockchain/fabric_network

Toàn bộ 116 sự kiện thử nghiệm đã được kiểm tra tồn tại trực tiếp trên Fabric ledger.

## 8. Kiểm tra tính toàn vẹn

Các chương trình chính:

    src/verify_integrity.py
    src/verify_all_blockchain_integrity.py
    src/test_tampering.py
    src/test_all_tampering.py

Kết quả:

- 116/116 sự kiện vượt qua kiểm tra tính toàn vẹn.
- 116/116 trường hợp giả lập thay đổi dữ liệu được phát hiện.
- Tỷ lệ phát hiện tampering: 100%.

## 9. SHACL và SPARQL

SHACL:

    03_ontology/shacl/traceability_shapes.ttl

SPARQL:

    03_ontology/sparql/blockchain_metadata_check.rq
    03_ontology/sparql/batch_journey.rq

Ontology cuối cùng vượt qua SHACL validation.

Metadata blockchain của 116 sự kiện được truy vấn thành công từ ontology.

## 10. Kết quả thực nghiệm

Blockchain:

    04_blockchain/results/experiment_summary.csv
    04_blockchain/results/query_performance.csv
    04_blockchain/results/write_performance.csv

Ontology:

    03_ontology/results/ontology_experiment_summary.csv
    03_ontology/results/ontology_statistics.csv
    03_ontology/results/reasoner_swrl_experiment.csv
    03_ontology/results/shacl_experiment.csv
    03_ontology/results/sparql_traceability_experiment.csv

## 11. Demo truy xuất

Ứng dụng:

    05_demo/web/app.py

Chạy:

    python 05_demo/web/app.py

QR được tạo cho 5 lô phân phối DL001-DL005.

QR URL sử dụng địa chỉ được cấu hình tại demo.base_url trong config.yaml.

Lưu ý: Cloudflare Quick Tunnel sử dụng URL tạm thời. Nếu URL thay đổi cần cập nhật demo.base_url và tạo lại QR URL.

## 12. Unit tests

Chạy:

    python -m unittest tests.tests_mapping -v

Bộ kiểm thử hiện có 8 test kiểm tra cấu trúc và tính hợp lệ của dữ liệu sự kiện.

## 13. Kết quả chính

- 116 TraceabilityEvent.
- 116/116 sự kiện tồn tại trên Hyperledger Fabric ledger.
- 116/116 sự kiện vượt qua kiểm tra toàn vẹn.
- 116/116 trường hợp giả lập tampering được phát hiện.
- SHACL validation đạt yêu cầu.
- SPARQL truy vấn thành công metadata blockchain của 116 sự kiện.
- Truy xuất được chuỗi nghiệp vụ từ nuôi đến phân phối.
- Demo QR/Web hoạt động cho DL001-DL005.
