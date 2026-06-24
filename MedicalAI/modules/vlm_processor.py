import pydicom
import io

def process_dicom_file(uploaded_file):
    """[함수 설명]: 업로드 컴포넌트가 전달한 파일 바이트 스트림을 pydicom 라이브러리를 통해 읽어 환자 메타데이터를 추출합니다."""

    try:
        uploaded_file.seek(0)

        dcm = pydicom.dcmread(io.BytesIO(uploaded_file.read()))

        patient_name = str(dcm.get("PatientName", "Unknown Patient"))
        patient_id = str(dcm.get("PatientID", "0000000"))
        study_date = str(dcm.get("StudyDate", "YYYYMMDD"))

        return {
            "success": True,
            "patient_name": patient_name,
            "patient_id": patient_id,
            "study_date": study_date
        }
    except Exception as e:
        return{
            "success":false,
            "error":str(e)
        }