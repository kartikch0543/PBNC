import os
import uuid
import pytest
from httpx import ASGITransport, AsyncClient

import app.core.database as db_core
from app.core.security import create_access_token
from app.main import app
from app.models.document import Document, DocumentType, ProcessingStatus
from app.models.question import AnswerSource, Question, QuestionStatus, QuestionType
from app.models.user import User


@pytest.mark.asyncio
async def test_review_question_workflow():
    """Verifies human review workflow: editing, marking reviewed, preserving original extraction."""
    await db_core.init_database()

    async with db_core.AsyncSessionLocal() as session:
        # Create user
        user = User(
            email=f"reviewer_{uuid.uuid4().hex[:8]}@example.com",
            hashed_password="hashed_test_pass",
            is_active=True,
        )
        session.add(user)
        await session.flush()

        # Create document
        doc = Document(
            user_id=user.id,
            original_filename="Exam.pdf",
            stored_filename=f"exam_{uuid.uuid4().hex[:8]}.pdf",
            file_path="uploads/exam.pdf",
            file_hash="dummyhash",
            file_size_bytes=1024,
            mime_type="application/pdf",
            document_type=DocumentType.QUESTION_PAPER,
            processing_status=ProcessingStatus.COMPLETED,
        )
        session.add(doc)
        await session.flush()

        # Create question requiring review
        q = Question(
            document_id=doc.id,
            question_number="1",
            question_text="Original blurry stem?",
            question_type=QuestionType.MULTIPLE_CHOICE,
            options=[{"key": "A", "text": "Wrong A"}, {"key": "B", "text": "Wrong B"}],
            detected_answer="A",
            confidence_score=0.45,
            status=QuestionStatus.REVIEW_REQUIRED,
            source_pages=[1],
        )
        session.add(q)
        await session.commit()
        await session.refresh(q)
        q_id = q.id
        u_id = str(user.id)

    token = create_access_token(subject=u_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Fetch question before review
        res_before = await client.get(
            f"/api/v1/questions/{q_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res_before.status_code == 200
        assert res_before.json()["is_reviewed"] is False

        # 2. Submit reviewer correction
        review_payload = {
            "question_text": "Corrected clear stem: Which is correct?",
            "options": [{"key": "A", "text": "Option A"}, {"key": "B", "text": "Correct Option B"}],
            "detected_answer": "B",
            "review_notes": "Corrected OCR misread and mapped answer to B based on Page 1 key.",
            "mark_reviewed": True,
        }
        review_res = await client.patch(
            f"/api/v1/questions/{q_id}/review",
            headers={"Authorization": f"Bearer {token}"},
            json=review_payload,
        )
        assert review_res.status_code == 200
        reviewed_data = review_res.json()

        assert reviewed_data["question_text"] == "Corrected clear stem: Which is correct?"
        assert reviewed_data["detected_answer"] == "B"
        assert reviewed_data["is_reviewed"] is True
        assert reviewed_data["review_notes"] is not None
        assert reviewed_data["confidence_score"] >= 0.95
        # Verify original extraction was preserved
        assert reviewed_data["original_extraction"] is not None
        assert reviewed_data["original_extraction"]["question_text"] == "Original blurry stem?"


@pytest.mark.asyncio
async def test_dashboard_stats():
    """Verifies that the dashboard aggregate statistics endpoint accurately computes counters."""
    await db_core.init_database()

    async with db_core.AsyncSessionLocal() as session:
        user = User(
            email=f"dash_user_{uuid.uuid4().hex[:8]}@example.com",
            hashed_password="hashed_test_pass",
            is_active=True,
        )
        session.add(user)
        await session.flush()

        doc = Document(
            user_id=user.id,
            original_filename="DashDoc.pdf",
            stored_filename=f"dash_{uuid.uuid4().hex[:8]}.pdf",
            file_path="uploads/dash.pdf",
            file_hash="dashhash",
            file_size_bytes=2048,
            mime_type="application/pdf",
            document_type=DocumentType.QUESTION_PAPER,
            processing_status=ProcessingStatus.COMPLETED,
        )
        session.add(doc)
        await session.flush()

        q1 = Question(
            document_id=doc.id,
            question_number="1",
            question_text="Q1 text",
            question_type=QuestionType.MULTIPLE_CHOICE,
            options=[{"key": "A", "text": "A"}],
            confidence_score=0.95,
            status=QuestionStatus.EXTRACTED,
            source_pages=[1],
        )
        q2 = Question(
            document_id=doc.id,
            question_number="2",
            question_text="Q2 text",
            question_type=QuestionType.MULTIPLE_CHOICE,
            options=[{"key": "A", "text": "A"}],
            confidence_score=0.50,
            status=QuestionStatus.REVIEW_REQUIRED,
            source_pages=[1],
        )
        session.add_all([q1, q2])
        await session.commit()
        u_id = str(user.id)

    token = create_access_token(subject=u_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            "/api/v1/dashboard/stats",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        stats = res.json()
        assert stats["total_documents"] >= 1
        assert stats["total_questions"] >= 2
        assert stats["review_required_count"] >= 1
        assert len(stats["recent_jobs"]) >= 1


@pytest.mark.asyncio
async def test_document_export_structured_output():
    """Verifies that GET /documents/{id}/export outputs clean Assignment Section 7 schema."""
    await db_core.init_database()

    async with db_core.AsyncSessionLocal() as session:
        user = User(
            email=f"export_user_{uuid.uuid4().hex[:8]}@example.com",
            hashed_password="hashed_test_pass",
            is_active=True,
        )
        session.add(user)
        await session.flush()

        doc = Document(
            user_id=user.id,
            original_filename="ExportTest.pdf",
            stored_filename=f"exp_{uuid.uuid4().hex[:8]}.pdf",
            file_path="uploads/exp.pdf",
            file_hash="exphash",
            file_size_bytes=1024,
            mime_type="application/pdf",
            document_type=DocumentType.QUESTION_PAPER,
            processing_status=ProcessingStatus.COMPLETED,
        )
        session.add(doc)
        await session.flush()

        q = Question(
            document_id=doc.id,
            question_number="1",
            question_text="Which layer is responsible for routing?",
            question_type=QuestionType.MULTIPLE_CHOICE,
            options=[
                {"key": "A", "text": "Physical"},
                {"key": "B", "text": "Network"},
                {"key": "C", "text": "Transport"},
            ],
            detected_answer="B",
            confidence_score=0.98,
            status=QuestionStatus.EXTRACTED,
            source_pages=[1, 2],
        )
        session.add(q)
        await session.commit()
        doc_id = str(doc.id)
        u_id = str(user.id)

    token = create_access_token(subject=u_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            f"/api/v1/documents/{doc_id}/export",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        item = data[0]
        assert item["question"] == "Which layer is responsible for routing?"
        assert item["options"] == ["Physical", "Network", "Transport"]
        assert item["answer"] == "B"
        assert item["source_pages"] == [1, 2]
        assert item["confidence"] == 0.98
