#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KRONOS - Testing de Componentes Individuales CLARO
==================================================

Test individual de cada componente para identificar issues específicos.
"""

import os
import sys
from pathlib import Path

# Set console encoding for Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

# Add backend to path
backend_path = Path(__file__).parent / "Backend"
sys.path.insert(0, str(backend_path))

def test_db_connection():
    """Test 1: Database connection"""
    print("🔗 Testing database connection...")
    try:
        from database.connection import get_db_connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT count(*) FROM operator_data_sheets")
            count = cursor.fetchone()[0]
            print(f"✅ Database connection OK. operator_data_sheets has {count} records")
            return True
    except Exception as e:
        print(f"❌ Database connection FAILED: {e}")
        return False

def test_operator_logger():
    """Test 2: Operator Logger"""
    print("📝 Testing operator logger...")
    try:
        from utils.operator_logger import OperatorLogger
        logger = OperatorLogger()
        logger.info("Test log message")
        print("✅ OperatorLogger OK")
        return True
    except Exception as e:
        print(f"❌ OperatorLogger FAILED: {e}")
        return False

def test_data_normalizer():
    """Test 3: Data Normalizer"""
    print("🔧 Testing data normalizer...")
    try:
        from services.data_normalizer_service import DataNormalizerService
        normalizer = DataNormalizerService()
        
        # Test with sample data
        test_record = {
            'numero': '573205487611',
            'fecha_trafico': '20240419080000',
            'tipo_cdr': 'DATOS',
            'celda_decimal': '175462',
            'lac_decimal': '20010'
        }
        
        normalized = normalizer.normalize_claro_cellular_data(
            test_record, 'test-file-id', 'test-mission-id'
        )
        
        if normalized and 'record_hash' in normalized:
            print("✅ DataNormalizerService OK")
            return True
        else:
            print("❌ DataNormalizerService FAILED: No normalized data returned")
            return False
    except Exception as e:
        print(f"❌ DataNormalizerService FAILED: {e}")
        return False

def test_file_processor():
    """Test 4: File Processor"""
    print("📄 Testing file processor...")
    try:
        from services.file_processor_service import FileProcessorService
        processor = FileProcessorService()
        
        # Test with sample CSV data
        test_data = "numero,fecha_trafico,tipo_cdr,celda_decimal,lac_decimal\n573123456789,20240419080000,DATOS,175462,20010\n"
        test_bytes = test_data.encode('utf-8')
        
        # Test encoding detection
        encoding = processor._detect_encoding(test_bytes)
        
        # Test CSV reading
        df = processor._read_csv_robust(test_bytes, delimiter=',')
        
        # Test validation
        is_valid, errors = processor._validate_claro_cellular_columns(df)
        
        if is_valid and len(df) > 0:
            print("✅ FileProcessorService OK")
            return True
        else:
            print(f"❌ FileProcessorService FAILED: Validation errors: {errors}")
            return False
    except Exception as e:
        print(f"❌ FileProcessorService FAILED: {e}")
        return False

def test_real_csv_parsing():
    """Test 5: Real CSV file parsing"""
    print("📊 Testing real CSV file...")
    try:
        csv_file = Path(__file__).parent / "datatest" / "Claro" / "DATOS_POR_CELDA CLARO.csv"
        
        if not csv_file.exists():
            print("⚠️ CSV file not found, skipping")
            return None
        
        from services.file_processor_service import FileProcessorService
        processor = FileProcessorService()
        
        with open(csv_file, 'rb') as f:
            # Read first 10KB for quick test
            file_bytes = f.read(10240)
        
        encoding = processor._detect_encoding(file_bytes)
        df = processor._read_csv_robust(file_bytes, delimiter=',')
        is_valid, errors = processor._validate_claro_cellular_columns(df)
        
        print(f"   📁 File size: {csv_file.stat().st_size / 1024:.1f} KB")
        print(f"   🔤 Encoding: {encoding}")
        print(f"   📋 Rows read: {len(df) if df is not None else 0}")
        print(f"   ✅ Valid structure: {is_valid}")
        
        if not is_valid:
            print(f"   ❌ Errors: {errors}")
            return False
        
        print("✅ Real CSV parsing OK")
        return True
        
    except Exception as e:
        print(f"❌ Real CSV parsing FAILED: {e}")
        return False

def test_integration_flow():
    """Test 6: End-to-end integration flow simulation"""
    print("🔄 Testing integration flow...")
    try:
        # Import all services
        from database.connection import get_db_connection
        from services.file_processor_service import FileProcessorService
        from services.data_normalizer_service import DataNormalizerService
        
        # Create test data
        test_csv = """numero,fecha_trafico,tipo_cdr,celda_decimal,lac_decimal
573205487611,20240419080000,DATOS,175462,20010
573133934909,20240419080001,DATOS,175463,20011"""
        
        file_bytes = test_csv.encode('utf-8')
        
        # Step 1: Process file
        processor = FileProcessorService()
        df = processor._read_csv_robust(file_bytes, delimiter=',')
        is_valid, errors = processor._validate_claro_cellular_columns(df)
        
        if not is_valid:
            print(f"❌ File validation failed: {errors}")
            return False
        
        # Step 2: Normalize data
        normalizer = DataNormalizerService()
        normalized_records = []
        
        for _, row in df.iterrows():
            record = row.to_dict()
            normalized = normalizer.normalize_claro_cellular_data(
                record, 'test-file-integration', 'test-mission-integration'
            )
            if normalized:
                normalized_records.append(normalized)
        
        # Step 3: Database interaction (test without actual insert)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Verify table structure
            cursor.execute("PRAGMA table_info(operator_cellular_data)")
            columns = [col[1] for col in cursor.fetchall()]
            
            required_columns = ['numero_telefono', 'fecha_hora_inicio', 'celda_id', 'operator']
            missing_cols = [col for col in required_columns if col not in columns]
            
            if missing_cols:
                print(f"❌ Missing database columns: {missing_cols}")
                return False
        
        print(f"   📊 Records processed: {len(normalized_records)}")
        print(f"   🏗️ Database schema: OK")
        print("✅ Integration flow OK")
        return True
        
    except Exception as e:
        print(f"❌ Integration flow FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all component tests"""
    print("🧪 KRONOS CLARO - Component Testing")
    print("=" * 60)
    
    tests = [
        test_db_connection,
        test_operator_logger,
        test_data_normalizer,
        test_file_processor,
        test_real_csv_parsing,
        test_integration_flow
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
        print()
    
    # Summary
    print("=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results if r is True)
    failed = sum(1 for r in results if r is False)
    skipped = sum(1 for r in results if r is None)
    
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️ Skipped: {skipped}")
    print(f"📊 Success Rate: {passed / (passed + failed) * 100:.1f}%" if (passed + failed) > 0 else "N/A")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️ {failed} TESTS FAILED")
        return 1

if __name__ == "__main__":
    exit(main())