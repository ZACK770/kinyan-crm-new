"""
Test script to verify all API endpoints are properly loaded and accessible.
"""
import sys
import importlib
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test that all API modules can be imported."""
    api_modules = [
        'leads_api', 'students_api', 'courses_api', 'dashboard_api', 'webhooks_api',
        'inquiries_api', 'exams_api', 'payments_api', 'expenses_api', 'attendance_api', 
        'collections_api', 'auth_api', 'users_api', 'audit_logs_api', 'campaigns_api', 
        'files_api', 'sales_assignment_api', 'course_tracks_api', 'lecturers_api', 
        'messages_api', 'templates_api', 'lead_conversion_api', 'chat_api',
        'salespeople_api', 'tasks_api', 'examinees_api', 'table_prefs_api', 
        'popup_api', 'webhook_logs_api', 'exam_registration_api', 'export_api', 
        'import_api', 'topics_api'
    ]
    
    print("Testing API module imports...")
    failed = []
    
    for module_name in api_modules:
        try:
            module = importlib.import_module(f'api.{module_name}')
            if hasattr(module, 'router'):
                print(f"✓ {module_name:30s} - OK")
            else:
                print(f"✗ {module_name:30s} - No router found")
                failed.append(module_name)
        except Exception as e:
            print(f"✗ {module_name:30s} - {str(e)[:60]}")
            failed.append(module_name)
    
    return failed

def test_models():
    """Test that all required models can be imported."""
    print("\nTesting model imports...")
    
    models_to_test = [
        'User', 'Lead', 'Student', 'Course', 'Exam', 'ExamSubmission',
        'ExamDate', 'ExamDateExam', 'Examinee', 'ExamRegistration',
        'ChatThread', 'ChatThreadMember', 'ChatMessage',
        'WebhookLog', 'PopupAnnouncement', 'PopupDismissal', 'GlobalTablePref',
        'Salesperson', 'Payment', 'Lecturer'
    ]
    
    failed = []
    
    try:
        from db import models
        for model_name in models_to_test:
            if hasattr(models, model_name):
                print(f"✓ {model_name:30s} - OK")
            else:
                print(f"✗ {model_name:30s} - Not found")
                failed.append(model_name)
    except Exception as e:
        print(f"✗ Failed to import db.models: {e}")
        return models_to_test
    
    return failed

def test_app_startup():
    """Test that the FastAPI app can be imported."""
    print("\nTesting FastAPI app import...")
    
    try:
        from app import app
        print(f"✓ FastAPI app imported successfully")
        print(f"  Routes registered: {len(app.routes)}")
        return True
    except Exception as e:
        print(f"✗ Failed to import app: {e}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("API Endpoints & Models Test")
    print("=" * 70)
    
    failed_imports = test_imports()
    failed_models = test_models()
    app_ok = test_app_startup()
    
    print("\n" + "=" * 70)
    print("Summary:")
    print("=" * 70)
    
    if failed_imports:
        print(f"✗ Failed API imports: {', '.join(failed_imports)}")
    else:
        print("✓ All API modules imported successfully")
    
    if failed_models:
        print(f"✗ Missing models: {', '.join(failed_models)}")
    else:
        print("✓ All models found")
    
    if app_ok:
        print("✓ FastAPI app loads successfully")
    else:
        print("✗ FastAPI app failed to load")
    
    # Exit with error code if any tests failed
    if failed_imports or failed_models or not app_ok:
        sys.exit(1)
    else:
        print("\n✓ All tests passed!")
        sys.exit(0)
