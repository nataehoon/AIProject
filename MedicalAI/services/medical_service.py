from modules.db_repository import execute_select_query, execute_non_query, execute_transaction_query
from models.mediinfo import Mediinfo, VersionInfo, QA_RawData, Paper_RawData
from datetime import datetime
from modules.sentence_transformer import encode, list_encode
from datasets import load_dataset
from config import QA_DATASET_MODEL, PAPER_DATASET_MODEL
from modules.dicomdir_processor import process_dicom_zip
from modules.ai_processor import run_vlm_generator, run_llm_generator
from services.rag_service import RAGService
import matplotlib.pyplot as plt
import io, base64

def _find_body_part(total_slices: int, target_modality: str, pixel_buffers):
    if total_slices > 5:
        if target_modality == "MR":
            target_indices = [int(total_slices * fraction) for fraction in [0.2, 0.4, 0.6, 0.8, 1.0]]
        else:
            target_indices = [int(total_slices * fraction) for fraction in [0.2, 0.4, 0.6, 0.8]]
    else:
        target_indices = list(range(total_slices))

    images_payload_array = []
    description = ""
    for slice_idx in target_indices:
        try:
            safe_idx = min(slice_idx, total_slices -1)
            matrix_np = pixel_buffers[target_modality][safe_idx]

            if isinstance(matrix_np, (int, float)) or matrix_np is None:
                print(f"[{target_modality}] 슬라이스 {safe_idx}번 데이터 유효성 실효: 스칼라 타입이 발견되어 스킵합니다.")
                continue

            plt.figure(figsize=[8, 8])
            plt.imshow(matrix_np, cmap=plt.cm.bone)
            plt.axis('off')

            memory_stream = io.BytesIO()

            plt.savefig(memory_stream, format='png', bbox_inches='tight', dpi=100)
            plt.close()

            base64_encoded = base64.b64encode(memory_stream.getvalue()).decode('utf-8')
            images_payload_array.append(base64_encoded)

            if target_modality == "CR":
                description += "This is a general X-ray (CR) view. Please evaluate the overall skeletal alignment and check for signs of dislocation."
            elif target_modality == "MR":
                description += f"This is a specific cross-sectional layer ({slice_idx}/{total_slices}) from the MRI volume. Please cross-analyze the condition of the rotator cuff tendons."
        except Exception as e:
            print(f"[target_modality] 슬라이스 {slice_idx} 랜더링 예외 발생: {e}")
            if 'plt' in locals() or 'plt' in globals():
                plt.close()

    if images_payload_array:
        vlm_prompt = """# Role & Context
                        You are an expert clinical image classifier. Your sole task is to analyze the provided sequential anatomical slice images and accurately classify which joint of the extremities is being imaged.

                        # Classification Target (body_part)
                        Classify the scan into exactly one of the following uppercase categories:
                        - `SHOULDER` (Look for the humeral head, glenoid cavity, clavicle, or acromion)
                        - `KNEE` (Look for the femur, tibia, patella, meniscus, or cruciate ligaments)
                        - `HIP` (Look for the femoral head, acetabulum, or pelvis)
                        - `ANKLE` (Look for the talus, tibia, fibula, or achilles tendon)
                        - `WRIST` (Look for the radius, ulna, carpal bones, or TFCC)
                        - `UNKOWN` (Use this if the anatomy does not clearly belong to any of the five joints above)

                        # Strict Formatting & Output Rules (Structured Output)
                        You must populate the JSON response properties exactly as defined below. Do not include any other markdown formatting or extra fields outside this schema:

                        1. **`body_part`** (String, Enum):
                        - Set this property to exactly one of the uppercase strings: `["SHOULDER", "KNEE", "HIP", "ANKLE", "WRIST", "UNKOWN"]`.

                        2. **`report_text`** (String):
                        - Do not write a comprehensive medical report. 
                        - Instead, write a single concise sentence explaining the visual evidence used for your classification. (e.g., "Identified the humeral head articulating with the glenoid cavity, confirming a shoulder scan.")

                        # Input Data
                        - A representative sample of sequential slice images from the scan.
                        """.strip()

        chatMessage = [{"role": "user", "content": vlm_prompt, "images": images_payload_array}]
        vlm_response = run_vlm_generator(chatMessage)

        body_part = ""
        for chunk in vlm_response:
            if chunk:
                body_part += chunk

        return body_part

def _vlm_detail_research(total_slices: int, target_modality: str, body_part: str, pixel_buffers):
    batch_size = 20
    overlap = 5
    step = batch_size - overlap
    vlm_text = ""
    for start in range(0, total_slices, step):
        if start + overlap >= total_slices and start > 0:
            break
        end = min(start + batch_size, total_slices)

        yield {"status": f"{target_modality}의 {start}~{end}번째 데이터를 분석 중 입니다..."}
        batch_images = []
        for slice_idx in range(start, end):
            try:
                safe_idx = min(slice_idx, total_slices -1)
                matrix_np = pixel_buffers[target_modality][safe_idx]

                if isinstance(matrix_np, (int, float)) or matrix_np is None:
                    print(f"[{target_modality}] 슬라이스 {safe_idx}번 데이터 유효성 실효: 스칼라 타입이 발견되어 스킵합니다.")
                    continue

                plt.figure(figsize=[8,8])
                plt.imshow(matrix_np, cmap=plt.cm.bone)
                plt.axis('off')

                memory_stream = io.BytesIO()

                plt.savefig(memory_stream, format='png', bbox_inches='tight', dpi=100)
                plt.close()

                base64_encoded = base64.b64encode(memory_stream.getvalue()).decode('utf-8')
                batch_images.append(base64_encoded)
            except Exception as e:
                print(f"[target_modality] 슬라이스 {slice_idx} 랜더링 예외 발생: {e}")
                if 'plt' in locals() or 'plt' in globals():
                    plt.close()

        research_prompt = f"""# Role & Context
                            You are an expert clinical image analyst with performance matching a senior neuroradiologist and musculoskeletal radiologist. Your task is to conduct a highly detailed, systematic review of the provided 20 sequential slice images, detect any subtle abnormalities or structural pathologies, and generate a comprehensive clinical reading report. Use precise anatomical terminology and base your reasoning strictly on visual evidence.

                            # Specifications
                            - Target Anatomy: `"{body_part}"`

                            # Rules
                            - Evaluate if there are any clinically significant abnormalities across these 20 slices.
                            - If NO abnormalities are detected, output EXACTLY the phrase `"No issues"` and absolutely nothing else.
                            - If ANY abnormality is detected, generate a detailed report using the "Report Structure" below.

                            # Report Structure (ONLY if an abnormality is detected)

                            ### 1. Overview & Image Specifications
                            - **Target Anatomy:** <BODY_PART_PLACEHOLDER>
                            - **Quality Assessment:** (Describe the clarity and spatial coverage of these 20 slices relative to the target anatomy)

                            ### 2. Slice-by-Slice Detailed Analysis
                            - **Slices [Start Index] to [End Index]:** Within normal limits. No significant structural abnormality or signal change detected.
                            - **Slice [Specific Index]:** 
                            - **Anatomical Landmark:** (e.g., Supraspinatus tendon, anterior horn of lateral meniscus, etc.)
                            - **Pathological Findings:** (Detailed signal intensity/density alterations, morphological tears, swelling, or bone marrow edema)
                            - **Spatial Continuity:** (Describe if this lesion connects or trend toward the boundary slices)

                            ### 3. Key Pathological Findings
                            1. **Localization & Dimensions:** (Specify the exact anatomical location and size/severity of the lesion/tear)
                            2. **Characteristics:** (Margin definition, presence of surrounding fluid accumulation, joint effusion, or mechanical compression)

                            ### 4. Clinical Impressions & Recommendations
                            - **Primary Impression:** (Most likely diagnosis)
                            - **Secondary Impression (Differential Diagnosis):** (Alternative pathologies to consider)
                            - **Recommended Next Steps:** (e.g., Contrast-enhanced evaluation, clinical correlation, or specific follow-up interval)
                            """.strip()
        
        research_dicom = [{"role": "user", "content": research_prompt, "images": batch_images}]
        vlm_response = run_vlm_generator(research_dicom)

        for chunk in vlm_response:
            if chunk:
                vlm_text += chunk
        
    if vlm_text:
        print(vlm_text)
        return vlm_text
    
class MedicalService:
    @staticmethod
    def get_my_mediinfo(id: int) -> list["Mediinfo"] | None:
        qeury = "SELECT * FROM mediinfo WHERE member_id=%s"
        params = (id,)

        raw_rows = execute_select_query(query=qeury, params=params)

        if not raw_rows:
            return None

        return [Mediinfo(**row) for row in raw_rows]

    @staticmethod
    def save_my_mediinfo(my_medi: Mediinfo) -> bool | None:
        query = "INSERT INTO mediinfo(member_id, modality, file_name, analyzed_text, body_part) VALUES(%s, %s, %s, %s, %s);"
        params = (my_medi.member_id, my_medi.modality, my_medi.file_name, my_medi.analyzed_text, my_medi.body_part)

        return execute_non_query(query, params)

    @staticmethod
    def get_version_info() -> list["VersionInfo"] | None:
        query = "SELECT * FROM prod_version_info"

        raw_rows = execute_select_query(query)

        if not raw_rows:
            return None

        return [VersionInfo(**row) for row in raw_rows]

    @staticmethod
    def get_raw_data() -> tuple[list[QA_RawData], list[Paper_RawData]] | None:
        query = "SELECT * FROM medical_qa_knowledge_staging ORDER BY CAST(version AS DATE) DESC;"
        qa_raw_rows = execute_select_query(query)
        if qa_raw_rows:
            qa_raw_list = [QA_RawData(**row) for row in qa_raw_rows]
        else:
            qa_raw_list = []

        query = "SELECT * FROM medical_paper_chunks_staging ORDER BY CAST(version AS DATE) DESC;"
        paper_raw_rows = execute_select_query(query)
        if paper_raw_rows:
            paper_raw_list = [Paper_RawData(**row) for row in paper_raw_rows]
        else:
            paper_raw_list = []

        return (qa_raw_list, paper_raw_list)

    @staticmethod
    def save_version_select(version: str):
        query = "INSERT INTO prod_version_info(version, active) VALUES(%s, %s) ON CONFLICT (version) DO UPDATE SET active = EXCLUDED.active"
        params = (version, True)

        result = execute_non_query(query, params)

        if result > 0:
            query = "UPDATE prod_version_info SET active = %s WHERE version != %s"
            params = (False, version)

            execute_non_query(query, params)

            query = "INSERT INTO medical_qa_knowledge_prod(question, answer, combined_content, specialty, embedding, create_at, version_id) " \
            "SELECT question, answer, combined_content, specialty, embedding, CURRENT_TIMESTAMP as create_at, (SELECT id FROM prod_version_info WHERE version = %s" \
                    ") as version_id from medical_qa_knowledge_staging WHERE version = %s"
            params = (version, version)

            execute_non_query(query, params)

            query = "INSERT INTO medical_paper_chunks_prod(document_name, page_number, chunk_index, chunk_content, embedding, create_at, version_id) " \
            "SELECT document_name, page_number, chunk_index, chunk_content, embedding, CURRENT_TIMESTAMP as create_at, (SELECT id FROM prod_version_info WHERE version = %s" \
                    ") as version_id from medical_paper_chunks_staging WHERE version = %s"
            params = (version, version)
            
            execute_non_query(query, params)

    @staticmethod
    def dicom_file_process(uploaded_file, user_id:str):
        medi_info = Mediinfo()
        medi_info.file_name = uploaded_file.name
        medi_info.member_id = user_id

        yield {"status": "DICOM파일의 분석을 시작합니다..."}
        dicom_info = process_dicom_zip(uploaded_file)
        if dicom_info["success"]:
            yield {"status": "DICOM 분석을 완료 하였습니다..."}
            pixel_buffers = dicom_info.get("pixel_buffer")
            body_part = dicom_info.get("body_part")

            medi_info.modality = ",".join(pixel_buffers)
            medi_info.body_part = body_part

            yield {"status": "파일 전처리를 시작합니다..."}
            vlm_report = ""
            for target_modality in pixel_buffers:
                total_slices = len(pixel_buffers[target_modality])

                if total_slices == 0:
                    raise ValueError("전송받은 픽셀 버퍼 내에 슬라이스가 존재하지 않습니다.")

                if body_part == "UNKNOWN":
                    medi_info.body_part = _find_body_part(total_slices, target_modality, pixel_buffers)
                    print(f"body_part: {body_part}")

                for chunk in _vlm_detail_research(total_slices, target_modality, body_part, pixel_buffers):
                    if isinstance(chunk, dict):
                        yield chunk
                    elif isinstance(chunk, str):
                        vlm_report += chunk

            print(f"vlm_report: {vlm_report}")
            yield {"status": "판독 데이터를 재검증 데이터를 조회 합니다..."}
            query_prompt = """You are generating a retrieval query for a medical knowledge base.

                            Given the structured imaging findings,

                            - Preserve all clinically significant abnormalities.
                            - Remove findings that are unlikely to improve retrieval unless they are diagnostically important.
                            - Do not invent findings.
                            - Produce one concise paragraph optimized for semantic retrieval.

                            Return only the query.
                            """.strip()
            queryMessage = [{"role": "system", "content": query_prompt}, {"role": "user", "content": vlm_report}]
            query_result = run_llm_generator(queryMessage)

            query_text = ""
            for query in query_result:
                if query:
                    query_text += query
            print(f"query_text: {query_text}")
            v_data = encode(query_text)

            sources = ["qa", "paper"]
            rag_data = RAGService.get_rag_data(v_data, sources)

            yield {"status": "재검증을 위한 데이터와 분석 데이터를 LLM에게 전송합니다..."}
            verification_prompt = f"""
                                You are a Senior Radiologist and a Medical Report Validation AI.\n
                                Your primary mission is to verify the [VLM Draft Interpretation] against the provided [Medical Guideline Reference Standard].\n\n
                                [RAG CONTEXT VALIDATION DIRECTIVE]:\n
                                - Carefully assess the semantic correlation between the [VLM Draft Interpretation] and the [Medical Guideline Reference Standard].\n
                                - IF the provided Guideline is irrelevant, inapplicable, or mismatches the anatomical site/pathology of the patient's case, you MUST COMPLETELY DISCARD the Guideline.\n
                                - Never let irrelevant guidelines alter, distort, or corrupt the accurate findings of the initial VLM draft interpretation. Depend solely on the verified imaging findings if a mismatch occurs.\n\n
                                [Medical Guideline Reference Standard]\n
                                {rag_data}\n\n
                                [Patient Metadata]\n
                                - Patient Name: {dicom_info['patient_name']} | ID: {dicom_info['patient_id']}\n\n
                                [VLM Draft Interpretation]\n
                                {vlm_report}\n\n
                                [Action Guidelines]\n
                                1. If the draft deviates from the reference standard, contains medical distortions (hallucinations), or shows logical contradictions, correct them strictly based on the reference standard.\n
                                2. Filter out any fictional disease names or diagnoses not explicitly stated in the reference standard that are based on excessive speculation.\n
                                3. The final output must be formatted as a structured 'Final Comprehensive Medical Report' including the patient metadata.\n
                                4. Exclude all validation processes, justifications, or introductory remarks. Output ONLY the body of the 'Final Medical Report'.
                                """.strip()

            chatMessage = [{"role": "user", "content": verification_prompt}]

            llm_result = run_llm_generator(chatMessage)

            llm_text = ""
            for chunk in llm_result:
                if chunk:
                    llm_text += chunk

            medi_info.analyzed_text = llm_text
            save_result = MedicalService.save_my_mediinfo(medi_info)
            if save_result:
                yield {"status": "성공적으로 분석 내용을 저장 하였습니다."}
        else:
            yield {"status": f"실패하였습니다. {dicom_info["error"]}"}

    @staticmethod
    def run_rag_pipeline():
        yield 1
        qa_dataset = load_dataset(QA_DATASET_MODEL, split="train[:200]")

        yield 2
        try:
            qa_texts = []
            for row in qa_dataset:
                question = row.get("question") or ""
                answer = row.get("answer") or ""
                if not question or not answer:
                    continue
                combined = f"Medical Question: {question.strip()}\nExpert Answer: {answer.strip()}"
                qa_texts.append(combined)

            qa_v_list = list_encode(qa_texts)
        except Exception as e:
            print(f"Q&A 전처리 error: {e}")

        yield 3
        now = datetime.now().strftime("%Y-%m-%d")
        qa_queries_and_params = []
        cleanup_query = "DELETE FROM medical_qa_knowledge_staging WHERE version = %s"
        cleanup_params = (now,)
        qa_queries_and_params.append((cleanup_query, cleanup_params))

        qa_query = "INSERT INTO medical_qa_knowledge_staging(question, answer, combined_content, specialty, embedding, version) VALUES(%s, %s, %s, %s, %s, %s);"
        for index, row in enumerate(qa_dataset):
            qa_param = (row['question'], row['answer'], qa_texts[index], "General", qa_v_list[index], now)
            qa_queries_and_params.append((qa_query, qa_param))

        qa_fifo_query = "DELETE FROM medical_qa_knowledge_staging WHERE version NOT IN (SELECT version FROM (SELECT DISTINCT version FROM medical_qa_knowledge_staging ORDER BY version DESC LIMIT 3) AS tmp);"
        qa_queries_and_params.append((qa_fifo_query, ()))

        execute_transaction_query(qa_queries_and_params)

        yield 4
        paper_dataset = load_dataset(PAPER_DATASET_MODEL, split="train[:200]")

        yield 5
        try:
            paper_chunks_data = []
            for paper in paper_dataset:
                title = paper["title"]
                abstract = paper["abstract"]

                page_num = 0
                chunk_size = 1000
                for start_idx in range(0, len(abstract), chunk_size):
                    page_num += 1
                    chunk_str = abstract[start_idx: start_idx + chunk_size]
                    paper_chunks_data.append({"title": title, "content": chunk_str, "page_num": page_num})

            chunk_texts = [item["content"] for item in paper_chunks_data]
            paper_v_list = list_encode(chunk_texts)
        except Exception as e:
            print(f"paper 전처리 error: {e}")

        yield 6
        paper_queries_and_params = []
        paper_clean_query = "DELETE FROM medical_paper_chunks_staging WHERE version = %s"
        paper_clean_param = (now,)
        paper_queries_and_params.append((paper_clean_query, paper_clean_param))

        paper_query = "INSERT INTO medical_paper_chunks_staging(document_name, page_number, chunk_index, chunk_content, embedding, version) VALUES(%s, %s, %s, %s, %s, %s);"
        for index, item in enumerate(paper_chunks_data):
            paper_params = (item["title"], item["page_num"], index, item["content"], paper_v_list[index], now)
            paper_queries_and_params.append((paper_query, paper_params))

        paper_fifo_query = "DELETE FROM medical_paper_chunks_staging WHERE version NOT IN (SELECT version FROM (SELECT DISTINCT version FROM medical_paper_chunks_staging ORDER BY version DESC LIMIT 3) AS tmp);"
        paper_queries_and_params.append((paper_fifo_query, ()))

        execute_transaction_query(paper_queries_and_params)
        yield 7