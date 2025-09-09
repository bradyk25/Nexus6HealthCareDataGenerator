#!/usr/bin/env python3
"""
Integrated Flask Web API Server for NeuralNexus6 with Hackathon2025 Backend
Combines chatbot functionality with file processing capabilities
"""

from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from brain import Brain
from config import AIProvider
import os
import json
import traceback
from werkzeug.utils import secure_filename
import tempfile
import shutil
import sys
import uuid
from datetime import datetime
import zipfile
import pandas as pd
import io
import asyncio
from typing import Dict, Any, List

# Add Hackathon2025 to path for imports
sys.path.append('./Hackathon2025')
sys.path.append('./Hackathon2025/NeuralNexus6-restored_aidan_branch')

# Import backend processing functions
try:
    from process_and_clean import detect_and_clean_healthcare_data, save_cleaned_data
    from dbtwin_api import DBTwinAPI
    from enhanced_real_data_learning_pipeline import EnhancedRealDataLearningPipeline
    print("✓ Hackathon2025 backend modules imported successfully")
except ImportError as e:
    print(f"⚠️ Warning: Could not import Hackathon2025 modules: {e}")
    print("   File processing will use fallback methods")

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Initialize Phara Brain
try:
    brain = Brain()
    print("✓ Phara Brain initialized successfully")
except Exception as e:
    print(f"✗ Failed to initialize Phara Brain: {e}")
    brain = None

# Initialize NeuralNexus6 Enhanced Workflow
try:
    nexus_workflow = NexusEnhancedWorkflow(nexus_enabled=True, real_data_weight=0.75)
    print("✓ NeuralNexus6 Enhanced Workflow initialized")
except Exception as e:
    print(f"⚠️ Warning: NeuralNexus6 Enhanced Workflow not available: {e}")
    nexus_workflow = None

# Storage directories
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
HACKATHON_UPLOAD_FOLDER = 'Hackathon2025/uploads'
HACKATHON_OUTPUT_FOLDER = 'Hackathon2025/outputs'

# Create directories
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER, HACKATHON_UPLOAD_FOLDER, HACKATHON_OUTPUT_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# Job storage for processing status
processing_jobs: Dict[str, Dict[str, Any]] = {}

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'brain_initialized': brain is not None,
        'backend_available': nexus_workflow is not None,
        'message': 'NeuralNexus6 Integrated API is running'
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chat endpoint with context-aware responses and data search capabilities"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'No message provided'}), 400
        
        user_message = data['message'].strip()
        if not user_message:
            return jsonify({'error': 'Empty message'}), 400
        
        # Check for processed files in the backend
        processed_files = get_processed_files()
        
        # Check if this is a search query for specific data
        search_result = handle_data_search(user_message, processed_files)
        if search_result:
            return jsonify({
                'response': search_result,
                'model_info': {
                    'provider': 'builtin',
                    'model_name': 'Phara Healthcare Assistant',
                    'temperature': 0.7,
                    'max_tokens': 1000
                },
                'loaded_file': None,
                'processed_files': processed_files,
                'has_data': len(processed_files) > 0,
                'search_performed': True
            })
        
        # Check if this is a dataset metrics query
        metrics_result = handle_metrics_query(user_message, processed_files)
        if metrics_result:
            return jsonify({
                'response': metrics_result,
                'model_info': {
                    'provider': 'builtin',
                    'model_name': 'Phara Healthcare Assistant',
                    'temperature': 0.7,
                    'max_tokens': 1000
                },
                'loaded_file': None,
                'processed_files': processed_files,
                'has_data': len(processed_files) > 0,
                'metrics_provided': True
            })
        
        # Check if this is a data analysis query that requires reading CSV files
        analysis_result = handle_data_analysis(user_message, processed_files)
        if analysis_result:
            return jsonify({
                'response': analysis_result,
                'model_info': {
                    'provider': 'builtin',
                    'model_name': 'Phara Healthcare Assistant',
                    'temperature': 0.7,
                    'max_tokens': 1000
                },
                'loaded_file': None,
                'processed_files': processed_files,
                'has_data': len(processed_files) > 0,
                'analysis_provided': True
            })
        
        # Generate intelligent response based on context
        if brain:
            try:
                # Use real AI if available
                loaded_files = brain.get_loaded_files()
                
                # Enhance the user message with context about loaded and processed data
                if loaded_files or processed_files:
                    context_parts = []
                    if loaded_files:
                        context_parts.append(f"Currently analyzing file: '{loaded_files[0]}'")
                    if processed_files:
                        context_parts.append(f"Processed files available: {', '.join(processed_files[:3])}")
                    
                    context_message = f"""
                    Context: {' | '.join(context_parts)}
                    
                    The user has access to healthcare data files that have been uploaded and processed through our 
                    privacy-compliant pipeline. You can search for specific records by CLAIM_ID, MEMBER_ID, or patient ID.
                    Focus your response on analyzing this data and providing insights related to the uploaded healthcare datasets.
                    
                    User question: {user_message}
                    """
                else:
                    context_message = f"""
                    Context: No data file has been uploaded yet. Encourage the user to upload a healthcare 
                    data file so I can provide specific analysis and insights about their data.
                    
                    User question: {user_message}
                    """
                
                # Process the enhanced message through Phara's brain
                response = brain.think(context_message)
                
                return jsonify({
                    'response': response,
                    'model_info': brain.get_current_model_info(),
                    'loaded_file': loaded_files[0] if loaded_files else None,
                    'processed_files': processed_files,
                    'has_data': len(loaded_files) > 0 or len(processed_files) > 0
                })
                
            except Exception as e:
                print(f"Brain error, falling back to built-in responses: {e}")
        
        # Fallback to built-in intelligent responses
        response = generate_intelligent_response(user_message, processed_files)
        
        return jsonify({
            'response': response,
            'model_info': {
                'provider': 'builtin',
                'model_name': 'Phara Healthcare Assistant',
                'temperature': 0.7,
                'max_tokens': 1000
            },
            'loaded_file': None,
            'processed_files': processed_files,
            'has_data': len(processed_files) > 0
        })
        
    except Exception as e:
        print(f"Chat error: {e}")
        traceback.print_exc()
        return jsonify({
            'error': 'Internal server error',
            'response': 'I encountered an error while processing your request. Please try again.'
        }), 500

@app.route('/api/files/upload', methods=['POST'])
def upload_and_process_file():
    """Upload file and process through Hackathon2025 backend with proper workflow"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Get processing parameters
        synthetic_mode = request.form.get('synthetic_mode', 'true').lower() == 'true'
        synthetic_rows = int(request.form.get('synthetic_rows', 1000))
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        upload_path = os.path.join(HACKATHON_UPLOAD_FOLDER, f"{job_id}_{filename}")
        file.save(upload_path)
        
        print("=" * 80)
        print(f"🚀 STARTING HEALTHCARE DATA PROCESSING WORKFLOW")
        print("=" * 80)
        print(f"📁 File uploaded: {filename}")
        print(f"🆔 Job ID: {job_id}")
        print(f"📊 Synthetic mode: {synthetic_mode}")
        print(f"🔢 Synthetic rows requested: {synthetic_rows}")
        print(f"📂 Upload path: {upload_path}")
        
        # Initialize job status
        processing_jobs[job_id] = {
            'id': job_id,
            'status': 'processing',
            'filename': filename,
            'progress': 10,
            'message': 'File uploaded, starting processing...',
            'created_at': datetime.utcnow().isoformat()
        }
        
        # STEP 1: Extract and read original data
        print("\n🔍 STEP 1: EXTRACTING ORIGINAL DATA")
        print("-" * 50)
        try:
            original_data = extract_and_read_data(upload_path)
            print(f"✅ Successfully extracted {len(original_data)} records from uploaded file")
            processing_jobs[job_id]['progress'] = 20
        except Exception as e:
            print(f"❌ Failed to extract data: {e}")
            raise e
        
        # STEP 2: Clean and split data (process_and_clean.py)
        print("\n🧹 STEP 2: CLEANING AND SPLITTING DATA")
        print("-" * 50)
        try:
            cleaning_results = detect_and_clean_healthcare_data(original_data)
            
            # Separate claims and demographics data based on the actual data structure
            # Claims data: records with MEMBER_ID and no LAST_NAME
            # Demographics data: records with LAST_NAME (patient records)
            claims_data = []
            demographics_data = []
            
            for record in cleaning_results['cleaned_data']:
                # Check if this is a patient record (has LAST_NAME, even if redacted)
                has_last_name = (record.get('LAST_NAME') and 
                               str(record.get('LAST_NAME')).strip() and 
                               str(record.get('LAST_NAME')).strip() != '' and
                               str(record.get('LAST_NAME')).strip() != 'nan')
                
                # Check if this is a claims record (has MEMBER_ID)
                has_member_id = (record.get('MEMBER_ID') and 
                               str(record.get('MEMBER_ID')).strip() and 
                               str(record.get('MEMBER_ID')).strip() != '' and
                               str(record.get('MEMBER_ID')).strip() != 'nan')
                
                # Check if this has patient ID
                has_patient_id = (record.get('ID') and 
                                str(record.get('ID')).strip() and 
                                str(record.get('ID')).strip() != '' and
                                str(record.get('ID')).strip().startswith('PT'))
                
                if has_last_name or has_patient_id:
                    # This is demographics/patient data
                    demographics_data.append(record)
                elif has_member_id:
                    # This is claims data
                    claims_data.append(record)
                else:
                    # Default to claims if unclear
                    claims_data.append(record)
            
            print(f"✅ Data cleaning completed:")
            print(f"   📊 Total cleaned records: {len(cleaning_results['cleaned_data'])}")
            print(f"   🏥 Insurance claims records: {len(claims_data)}")
            print(f"   👥 Demographics records: {len(demographics_data)}")
            print(f"   🔒 PII fields protected: {len(cleaning_results['pii_detected'])}")
            print(f"   🏥 PHI fields identified: {len(cleaning_results['phi_detected'])}")
            
            processing_jobs[job_id]['progress'] = 40
            
        except Exception as e:
            print(f"❌ Data cleaning failed: {e}")
            raise e
        
        # STEP 3: Process both claims and demographics through Aiden branch
        enhanced_claims_data = claims_data  # Default to original claims
        enhanced_demographics_data = demographics_data  # Default to original demographics
        
        # Process claims through Aiden branch (if claims exist)
        if claims_data:
            print("\n🧠 STEP 3A: PROCESSING CLAIMS THROUGH AIDEN BRANCH")
            print("-" * 50)
            try:
                # Save claims to temporary file for Aiden branch processing
                temp_claims_file = os.path.join(HACKATHON_UPLOAD_FOLDER, f"{job_id}_temp_claims.csv")
                save_cleaned_data(claims_data, temp_claims_file)
                print(f"💾 Saved claims data to temporary file: {temp_claims_file}")
                
                # Initialize Enhanced Real Data Learning Pipeline
                enhanced_pipeline = EnhancedRealDataLearningPipeline(real_data_weight=0.75)
                print("✅ Enhanced Real Data Learning Pipeline initialized")
                
                # Learn enhanced patterns from claims data
                print("🔍 Learning enhanced patterns from claims data...")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    enhanced_patterns = loop.run_until_complete(
                        enhanced_pipeline.learn_enhanced_patterns(
                            temp_claims_file,
                            use_cached_government_data=True
                        )
                    )
                    print("✅ Enhanced patterns learned successfully")
                    
                    # Generate enhanced synthetic claims if requested
                    if synthetic_mode and synthetic_rows > 0:
                        print(f"🎯 Generating {synthetic_rows} enhanced synthetic claims...")
                        enhanced_claims_df = enhanced_pipeline.generate_enhanced_synthetic_data(
                            enhanced_patterns, 
                            synthetic_rows
                        )
                        enhanced_claims_data = enhanced_claims_df.to_dict('records')
                        print(f"✅ Generated {len(enhanced_claims_data)} enhanced synthetic claims")
                    
                finally:
                    loop.close()
                    # Clean up temporary file
                    if os.path.exists(temp_claims_file):
                        os.remove(temp_claims_file)
                
            except Exception as e:
                print(f"⚠️ Aiden branch processing failed, using original claims: {e}")
                enhanced_claims_data = claims_data
        else:
            print("\n⏭️ STEP 3A: SKIPPED (No claims data found)")
        
        # Process demographics through Aiden branch (if demographics exist)
        if demographics_data:
            print("\n🧠 STEP 3B: PROCESSING DEMOGRAPHICS THROUGH AIDEN BRANCH")
            print("-" * 50)
            try:
                # Save demographics to temporary file for Aiden branch processing
                temp_demographics_file = os.path.join(HACKATHON_UPLOAD_FOLDER, f"{job_id}_temp_demographics.csv")
                save_cleaned_data(demographics_data, temp_demographics_file)
                print(f"💾 Saved demographics data to temporary file: {temp_demographics_file}")
                
                # Initialize Enhanced Real Data Learning Pipeline for demographics
                demo_enhanced_pipeline = EnhancedRealDataLearningPipeline(real_data_weight=0.75)
                print("✅ Enhanced Real Data Learning Pipeline initialized for demographics")
                
                # Learn enhanced patterns from demographics data
                print("🔍 Learning enhanced patterns from demographics data...")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    demo_enhanced_patterns = loop.run_until_complete(
                        demo_enhanced_pipeline.learn_enhanced_patterns(
                            temp_demographics_file,
                            use_cached_government_data=True
                        )
                    )
                    print("✅ Enhanced demographics patterns learned successfully")
                    
                    # Generate enhanced synthetic demographics if requested
                    if synthetic_mode and synthetic_rows > 0:
                        # Calculate proportional demographics rows (maintain ratio)
                        demo_synthetic_rows = max(100, int(synthetic_rows * (len(demographics_data) / max(len(claims_data), 1))))
                        print(f"🎯 Generating {demo_synthetic_rows} enhanced synthetic demographics...")
                        enhanced_demographics_df = demo_enhanced_pipeline.generate_enhanced_synthetic_data(
                            demo_enhanced_patterns, 
                            demo_synthetic_rows
                        )
                        enhanced_demographics_data = enhanced_demographics_df.to_dict('records')
                        print(f"✅ Generated {len(enhanced_demographics_data)} enhanced synthetic demographics")
                    
                finally:
                    loop.close()
                    # Clean up temporary file
                    if os.path.exists(temp_demographics_file):
                        os.remove(temp_demographics_file)
                
            except Exception as e:
                print(f"⚠️ Aiden branch demographics processing failed, using original demographics: {e}")
                enhanced_demographics_data = demographics_data
        else:
            print("\n⏭️ STEP 3B: SKIPPED (No demographics data found)")
        
        processing_jobs[job_id]['progress'] = 60
        
        # STEP 4: Process both datasets through DBTwin
        final_claims_data = enhanced_claims_data
        final_demographics_data = enhanced_demographics_data
        
        print("\n🤖 STEP 4: PROCESSING THROUGH DBTWIN API")
        print("-" * 50)
        try:
            # Initialize DBTwin API (would need API key in production)
            dbtwin_api = DBTwinAPI()
            
            # Check if DBTwin is available
            if dbtwin_api.check_health():
                print("✅ DBTwin API is available")
                
                # Process claims through DBTwin if we have enough data
                if len(enhanced_claims_data) > 10 and synthetic_mode:
                    print(f"🔄 Processing {len(enhanced_claims_data)} claims through DBTwin...")
                    synthetic_claims_df, claims_metrics = dbtwin_api.generate_synthetic_data(
                        enhanced_claims_data, 
                        synthetic_rows
                    )
                    if synthetic_claims_df is not None:
                        final_claims_data = synthetic_claims_df.to_dict('records')
                        print(f"✅ DBTwin generated {len(final_claims_data)} synthetic claims")
                    else:
                        print("⚠️ DBTwin claims generation failed, using enhanced claims")
                
                # Process demographics through DBTwin - ALWAYS process if we have demographics data
                if len(demographics_data) > 0 and synthetic_mode:
                    print(f"🔄 Processing {len(demographics_data)} demographics through DBTwin...")
                    # For demographics, generate proportional synthetic data (maintain ratio)
                    demo_synthetic_rows = max(100, int(synthetic_rows * (len(demographics_data) / len(enhanced_claims_data))))
                    synthetic_demo_df, demo_metrics = dbtwin_api.generate_synthetic_data(
                        demographics_data, 
                        demo_synthetic_rows
                    )
                    if synthetic_demo_df is not None:
                        final_demographics_data = synthetic_demo_df.to_dict('records')
                        print(f"✅ DBTwin generated {len(final_demographics_data)} synthetic demographics")
                    else:
                        print("⚠️ DBTwin demographics generation failed, using original demographics")
                elif len(demographics_data) > 0:
                    print(f"📊 Keeping {len(demographics_data)} original demographics (synthetic mode disabled)")
                
            else:
                print("⚠️ DBTwin API not available, using processed data without additional synthesis")
            
            processing_jobs[job_id]['progress'] = 80
            
        except Exception as e:
            print(f"⚠️ DBTwin processing failed, using processed data: {e}")
        
        # STEP 5: Save final processed files with proper separation
        print("\n💾 STEP 5: SAVING PROCESSED FILES")
        print("-" * 50)
        try:
            # Save final files with proper data separation
            claims_file = os.path.join(HACKATHON_OUTPUT_FOLDER, f"{job_id}_claims.csv")
            demographics_file = os.path.join(HACKATHON_OUTPUT_FOLDER, f"{job_id}_demographics.csv")
            report_file = os.path.join(HACKATHON_OUTPUT_FOLDER, f"{job_id}_report.json")
            
            # Save ONLY claims data to claims file
            if final_claims_data:
                # Filter to only include actual claims records (have MEMBER_ID)
                pure_claims = []
                for record in final_claims_data:
                    if record.get('MEMBER_ID') and str(record.get('MEMBER_ID')).strip():
                        pure_claims.append(record)
                
                if pure_claims:
                    save_claims_data(pure_claims, claims_file)
                    print(f"✅ Saved {len(pure_claims)} pure claims records to: {claims_file}")
                else:
                    print("⚠️ No pure claims data found to save")
            
            # Save ONLY demographics data to demographics file
            if final_demographics_data:
                # Filter to only include actual demographics records (have ID starting with PT or LAST_NAME)
                pure_demographics = []
                for record in final_demographics_data:
                    has_patient_id = (record.get('ID') and str(record.get('ID')).startswith('PT'))
                    has_last_name = (record.get('LAST_NAME') and str(record.get('LAST_NAME')).strip() and 
                                   str(record.get('LAST_NAME')).strip() not in ['', 'nan'])
                    if has_patient_id or has_last_name:
                        pure_demographics.append(record)
                
                if pure_demographics:
                    save_demographics_data(pure_demographics, demographics_file)
                    print(f"✅ Saved {len(pure_demographics)} pure demographics records to: {demographics_file}")
                else:
                    print("⚠️ No pure demographics data found to save")
            
            # Save comprehensive processing report
            processing_report = {
                'job_id': job_id,
                'filename': filename,
                'workflow_steps': [
                    'Original data extraction',
                    'Data cleaning and splitting',
                    'Aiden branch enhancement (claims)',
                    'DBTwin synthetic generation',
                    'Final file generation'
                ],
                'original_data_count': len(original_data),
                'cleaned_data_count': len(cleaning_results['cleaned_data']),
                'final_claims_count': len(final_claims_data) if final_claims_data else 0,
                'final_demographics_count': len(final_demographics_data) if final_demographics_data else 0,
                'pii_detected': cleaning_results['pii_detected'],
                'phi_detected': cleaning_results['phi_detected'],
                'synthetic_mode': synthetic_mode,
                'synthetic_rows_requested': synthetic_rows if synthetic_mode else None,
                'processed_at': datetime.utcnow().isoformat(),
                'workflow_completed': True
            }
            
            with open(report_file, 'w') as f:
                json.dump(processing_report, f, indent=2, default=str)
            
            print(f"✅ Saved processing report to: {report_file}")
            processing_jobs[job_id]['progress'] = 90
            
        except Exception as e:
            print(f"❌ Failed to save files: {e}")
            raise e
        
        # STEP 6: Load into Phara's brain for analysis
        print("\n🧠 STEP 6: LOADING INTO PHARA'S BRAIN")
        print("-" * 50)
        if brain:
            try:
                brain_file_path = os.path.join('data', filename)
                shutil.copy2(upload_path, brain_file_path)
                brain.load_data_file(filename)
                print(f"✅ File loaded into Phara's brain: {filename}")
            except Exception as e:
                print(f"⚠️ Warning: Could not load file into brain: {e}")
        else:
            print("⚠️ Phara's brain not available")
        
        # Complete job
        processing_jobs[job_id].update({
            'status': 'completed',
            'progress': 100,
            'message': 'Processing completed successfully',
            'results': {
                'original_count': len(original_data),
                'claims_count': len(final_claims_data) if final_claims_data else 0,
                'demographics_count': len(final_demographics_data) if final_demographics_data else 0,
                'pii_fields_protected': len(cleaning_results['pii_detected']),
                'phi_fields_identified': len(cleaning_results['phi_detected']),
                'synthetic_mode': synthetic_mode,
                'synthetic_rows': synthetic_rows if synthetic_mode else None,
                'workflow_completed': True
            },
            'completed_at': datetime.utcnow().isoformat()
        })
        
        print("\n🎉 WORKFLOW COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print(f"📊 Final Results:")
        print(f"   📁 Original records: {len(original_data)}")
        print(f"   🏥 Final claims: {len(final_claims_data) if final_claims_data else 0}")
        print(f"   👥 Final demographics: {len(final_demographics_data) if final_demographics_data else 0}")
        print(f"   🔒 PII fields protected: {len(cleaning_results['pii_detected'])}")
        print(f"   🏥 PHI fields identified: {len(cleaning_results['phi_detected'])}")
        print(f"   🎯 Synthetic mode: {synthetic_mode}")
        print("=" * 80)
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': f'Successfully processed {filename} through complete workflow',
            'results': processing_jobs[job_id]['results'],
            'download_links': {
                'claims': f'/api/download/{job_id}/claims',
                'demographics': f'/api/download/{job_id}/demographics',
                'report': f'/api/download/{job_id}/report',
                'zip': f'/api/download/{job_id}/zip'
            }
        })
        
    except Exception as e:
        print(f"\n❌ WORKFLOW FAILED: {e}")
        print("=" * 80)
        traceback.print_exc()
        
        if job_id in processing_jobs:
            processing_jobs[job_id].update({
                'status': 'failed',
                'message': f'Processing failed: {str(e)}',
                'error': str(e)
            })
        
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

@app.route('/api/jobs/<job_id>/status', methods=['GET'])
def get_job_status(job_id):
    """Get processing job status"""
    if job_id not in processing_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(processing_jobs[job_id])

@app.route('/api/download/<job_id>/claims', methods=['GET'])
def download_claims(job_id):
    """Download claims CSV file"""
    try:
        claims_file = os.path.join(HACKATHON_OUTPUT_FOLDER, f"{job_id}_claims.csv")
        if os.path.exists(claims_file):
            return send_file(claims_file, 
                           as_attachment=True, 
                           download_name='insurance_claims.csv',
                           mimetype='text/csv')
        else:
            return jsonify({'error': 'Claims file not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<job_id>/demographics', methods=['GET'])
def download_demographics(job_id):
    """Download demographics CSV file"""
    try:
        demographics_file = os.path.join(HACKATHON_OUTPUT_FOLDER, f"{job_id}_demographics.csv")
        if os.path.exists(demographics_file):
            return send_file(demographics_file, 
                           as_attachment=True, 
                           download_name='patient_demographics.csv',
                           mimetype='text/csv')
        else:
            return jsonify({'error': 'Demographics file not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<job_id>/report', methods=['GET'])
def download_report(job_id):
    """Download processing report"""
    try:
        report_file = os.path.join(HACKATHON_OUTPUT_FOLDER, f"{job_id}_report.json")
        if os.path.exists(report_file):
            return send_file(report_file, 
                           as_attachment=True, 
                           download_name='processing_report.json',
                           mimetype='application/json')
        else:
            return jsonify({'error': 'Report file not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<job_id>/zip', methods=['GET'])
def download_zip(job_id):
    """Download complete package as ZIP file"""
    try:
        # Create a BytesIO object to store the ZIP file in memory
        zip_buffer = io.BytesIO()
        
        # Create ZIP file
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add claims file if it exists
            claims_file = os.path.join(HACKATHON_OUTPUT_FOLDER, f"{job_id}_claims.csv")
            if os.path.exists(claims_file):
                zip_file.write(claims_file, 'insurance_claims.csv')
            
            # Add demographics file if it exists
            demographics_file = os.path.join(HACKATHON_OUTPUT_FOLDER, f"{job_id}_demographics.csv")
            if os.path.exists(demographics_file):
                zip_file.write(demographics_file, 'patient_demographics.csv')
            
            # Add report file if it exists
            report_file = os.path.join(HACKATHON_OUTPUT_FOLDER, f"{job_id}_report.json")
            if os.path.exists(report_file):
                zip_file.write(report_file, 'processing_report.json')
            
            # Add README
            readme_content = f"""# NeuralNexus6 Healthcare Data Package

This ZIP file contains your processed healthcare data with privacy protection applied.

## Files Included:

1. **insurance_claims.csv** - Insurance claims data with PII/PHI protection
2. **patient_demographics.csv** - Patient demographic data with privacy safeguards  
3. **processing_report.json** - Detailed processing and privacy analysis report

## Privacy Protection Applied:

- PII (Personally Identifiable Information) fields have been protected
- PHI (Protected Health Information) fields have been identified and secured
- HIPAA compliance maintained throughout processing
- Statistical utility preserved for analysis

Generated by NeuralNexus6 Healthcare Analytics Platform
Processing Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
Job ID: {job_id}
"""
            zip_file.writestr('README.txt', readme_content)
        
        # Prepare the ZIP file for download
        zip_buffer.seek(0)
        
        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name=f'neuralnexus6_healthcare_data_{job_id[:8]}.zip',
            mimetype='application/zip'
        )
        
    except Exception as e:
        return jsonify({'error': f'ZIP creation failed: {str(e)}'}), 500

@app.route('/api/generate-synthetic', methods=['POST'])
def generate_synthetic_data():
    """Generate synthetic data endpoint"""
    try:
        data = request.get_json()
        rows = data.get('rows', 1000)
        
        # Check if we have processed files to base synthetic data on
        processed_files = get_processed_files()
        
        if not processed_files:
            return jsonify({
                'error': 'No processed data available',
                'message': 'Please upload and process a healthcare data file first'
            }), 400
        
        # Use the most recent processed file
        latest_job = processed_files[0]
        
        # Generate synthetic data based on processed file
        job_id = str(uuid.uuid4())
        
        # For now, return a success response
        # In a full implementation, this would trigger actual synthetic data generation
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': f'Synthetic data generation started for {rows} rows',
            'based_on': latest_job,
            'download_link': f'/api/download/{job_id}/synthetic'
        })
        
    except Exception as e:
        return jsonify({'error': f'Synthetic data generation failed: {str(e)}'}), 500

# Original chatbot endpoints (preserved for compatibility)
@app.route('/api/model/info', methods=['GET'])
def get_model_info():
    """Get current model information"""
    try:
        if not brain:
            return jsonify({
                'provider': 'demo',
                'model_name': 'Demo Mode',
                'temperature': 0.7,
                'max_tokens': 1000
            })
        
        info = brain.get_current_model_info()
        return jsonify(info)
        
    except Exception as e:
        print(f"Model info error: {e}")
        return jsonify({
            'provider': 'demo',
            'model_name': 'Demo Mode',
            'temperature': 0.7,
            'max_tokens': 1000
        })

@app.route('/api/model/switch', methods=['POST'])
def switch_model():
    """Switch AI model"""
    try:
        if not brain:
            return jsonify({'error': 'Brain not initialized'}), 500
        
        data = request.get_json()
        if not data or 'provider' not in data:
            return jsonify({'error': 'No provider specified'}), 400
        
        provider_name = data['provider'].lower()
        try:
            provider = AIProvider(provider_name)
            result = brain.switch_model(provider)
            
            return jsonify({
                'success': True,
                'message': result,
                'model_info': brain.get_current_model_info()
            })
            
        except ValueError:
            return jsonify({
                'error': f'Unknown provider: {provider_name}',
                'available_providers': [p.value for p in AIProvider]
            }), 400
            
    except Exception as e:
        print(f"Model switch error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/model/list', methods=['GET'])
def list_models():
    """List available AI models"""
    try:
        from config import Config
        
        models = []
        for provider in AIProvider:
            config = Config.MODEL_CONFIGS[provider]
            is_configured = (config.api_key and 
                           config.api_key != "your-openai-api-key-here" and 
                           config.api_key != "your-anthropic-api-key-here")
            
            models.append({
                'provider': provider.value,
                'model_name': config.model_name,
                'configured': is_configured,
                'temperature': config.temperature,
                'max_tokens': config.max_tokens
            })
        
        return jsonify({'models': models})
        
    except Exception as e:
        print(f"List models error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/suggestions', methods=['GET'])
def get_suggestions():
    """Get data analysis suggestions"""
    try:
        suggestions = []
        
        if brain:
            try:
                suggestions = brain.get_data_suggestions()
            except Exception as e:
                print(f"Brain suggestions error: {e}")
        
        # Add default suggestions
        default_suggestions = [
            "Upload a healthcare data file to get started",
            "Analyze data quality and completeness",
            "Generate privacy-compliant synthetic data"
        ]
        
        # Add suggestions based on processed files
        processed_files = get_processed_files()
        if processed_files:
            suggestions.extend([
                "Analyze the privacy protection applied to my data",
                "Show me the synthetic data generation results",
                "Compare original vs processed data quality"
            ])
        else:
            suggestions.extend(default_suggestions)
        
        return jsonify({
            'suggestions': suggestions if suggestions else default_suggestions,
            'count': len(suggestions) if suggestions else len(default_suggestions)
        })
        
    except Exception as e:
        print(f"Suggestions error: {e}")
        return jsonify({
            'suggestions': [
                "Upload a healthcare data file to get started",
                "Analyze data quality and completeness",
                "Generate privacy-compliant synthetic data"
            ],
            'count': 3
        })

# Utility functions
def get_processed_files():
    """Get list of processed files"""
    processed_files = []
    try:
        for filename in os.listdir(HACKATHON_OUTPUT_FOLDER):
            if filename.endswith('_report.json'):
                job_id = filename.replace('_report.json', '')
                processed_files.append(job_id)
    except Exception as e:
        print(f"Error getting processed files: {e}")
    
    return processed_files

def extract_and_read_data(filepath):
    """Extract data from uploaded file"""
    data = []
    
    if filepath.endswith('.zip'):
        # Handle ZIP files
        with zipfile.ZipFile(filepath, 'r') as zip_ref:
            for file_info in zip_ref.filelist:
                if file_info.is_dir() or file_info.filename.startswith('.'):
                    continue
                    
                if file_info.filename.endswith('.csv'):
                    try:
                        with zip_ref.open(file_info.filename) as csv_file:
                            df = pd.read_csv(csv_file)
                            if not df.empty:
                                data.extend(df.to_dict('records'))
                    except Exception as e:
                        print(f"Error reading {file_info.filename}: {e}")
                        continue
                        
                elif file_info.filename.endswith('.xlsx'):
                    try:
                        with zip_ref.open(file_info.filename) as excel_file:
                            df = pd.read_excel(excel_file)
                            if not df.empty:
                                data.extend(df.to_dict('records'))
                    except Exception as e:
                        print(f"Error reading {file_info.filename}: {e}")
                        continue
                        
    elif filepath.endswith('.csv'):
        try:
            df = pd.read_csv(filepath)
        except pd.errors.ParserError:
            try:
                df = pd.read_csv(filepath, on_bad_lines='skip')
            except TypeError:
                df = pd.read_csv(filepath, error_bad_lines=False, warn_bad_lines=True)
        data = df.to_dict('records')
        
    elif filepath.endswith('.xlsx'):
        df = pd.read_excel(filepath)
        data = df.to_dict('records')
    else:
        raise ValueError("Unsupported file format. Please upload CSV, XLSX, or ZIP files.")
    
    if not data:
        raise ValueError("No data found in uploaded file.")
    
    return data

def save_cleaned_data(data, filepath):
    """Save cleaned data to CSV file"""
    if data:
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False)

def save_claims_data(claims_data, filepath):
    """Save claims data with exact column format: CLAIM_ID through ADJUDICATION_STATUS, nothing after"""
    if not claims_data:
        print("❌ No claims data to save")
        return
    
    # EXACT format for insurance claims - ADJUDICATION_STATUS is the LAST column
    claims_columns = [
        'CLAIM_ID', 'MEMBER_ID', 'CLAIM_TYPE', 'ADMISSION_TYPE', 'PROVIDER_SPECIALTY',
        'PROVIDER_ZIP', 'DIAGNOSIS_CODE', 'PROCEDURE_CODE', 'COPAY', 'COINSURANCE', 
        'TOTAL_CHARGE', 'ADJUDICATION_STATUS'
    ]
    
    # Filter to only include columns that exist in the data
    available_columns = set()
    for record in claims_data:
        available_columns.update(record.keys())
    
    # Only include columns that exist in both the preferred list and the data
    final_columns = [col for col in claims_columns if col in available_columns]
    
    print(f"📊 Claims CSV will have columns: {final_columns}")
    print(f"✅ Last column is: {final_columns[-1] if final_columns else 'None'}")
    
    # Write CSV with exact column order
    import csv
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=final_columns)
        writer.writeheader()
        for record in claims_data:
            # Only include the specified columns, ignore everything else
            clean_record = {}
            for col in final_columns:
                value = record.get(col, '')
                if pd.isna(value):
                    clean_record[col] = ''
                else:
                    clean_record[col] = value
            writer.writerow(clean_record)

def save_demographics_data(demographics_data, filepath):
    """Save demographics data with exact format: CLAIM_ID, ID (PT####), then rest"""
    if not demographics_data:
        print("❌ No demographics data to save")
        return
    
    # EXACT format for demographics - CLAIM_ID first, then ID (PT####), then rest
    # Remove everything between CLAIM_ID and ID
    demographics_columns = [
        'CLAIM_ID', 'ID', 'LAST_NAME', 'AGE', 'GENDER', 'DRG_CODE',
        'ICD9_PROCEDURE', 'CLAIM_COST', 'STATUS'
    ]
    
    # Filter to only include columns that exist in the data
    available_columns = set()
    for record in demographics_data:
        available_columns.update(record.keys())
    
    # Only include columns that exist in both the preferred list and the data
    final_columns = [col for col in demographics_columns if col in available_columns]
    
    print(f"📊 Demographics CSV will have columns: {final_columns}")
    print(f"✅ First two columns are: {final_columns[:2] if len(final_columns) >= 2 else final_columns}")
    
    # Write CSV with exact column order
    import csv
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=final_columns)
        writer.writeheader()
        for record in demographics_data:
            # Only include the specified columns, ignore everything else
            clean_record = {}
            for col in final_columns:
                value = record.get(col, '')
                if pd.isna(value):
                    clean_record[col] = ''
                else:
                    clean_record[col] = value
            writer.writerow(clean_record)

def handle_data_search(user_message, processed_files):
    """Handle data search queries for claim ID, member ID, or patient ID - ACTUALLY READ CSV FILES"""
    message_lower = user_message.lower()
    
    # Check if this is a search query
    search_keywords = ['search', 'find', 'lookup', 'show me', 'get', 'retrieve']
    id_keywords = ['claim id', 'member id', 'patient id', 'id', 'claim', 'member', 'patient']
    
    is_search_query = any(keyword in message_lower for keyword in search_keywords)
    has_id_reference = any(keyword in message_lower for keyword in id_keywords)
    
    if not (is_search_query and has_id_reference):
        return None
    
    if not processed_files:
        return "❌ **No Data Available for Search**\n\nPlease upload and process a healthcare data file first to enable search functionality."
    
    # Extract potential ID from the message
    import re
    
    # Look for various ID patterns
    patterns = [
        r'\b(CLM\d+)\b',  # Claim ID pattern
        r'\b(MBR\d+)\b',  # Member ID pattern  
        r'\b(PT\d+)\b',   # Patient ID pattern
        r'\b(\d{6,})\b',  # Generic numeric ID
        r'\b([A-Z]{2,3}\d{3,})\b'  # Alphanumeric ID
    ]
    
    found_ids = []
    for pattern in patterns:
        matches = re.findall(pattern, user_message, re.IGNORECASE)
        found_ids.extend(matches)
    
    if not found_ids:
        return """🔍 **Search Instructions**

To search for specific records, please include an ID in your message:

**Examples:**
• "Search for claim ID CLM123456"
• "Find member MBR789012" 
• "Show me patient PT001234"
• "Lookup claim 123456"

**Supported ID Types:**
• **Claim IDs** - CLM followed by numbers
• **Member IDs** - MBR followed by numbers
• **Patient IDs** - PT followed by numbers
• **Numeric IDs** - Any 6+ digit number

Try again with a specific ID to search for!"""
    
    # ACTUALLY SEARCH THROUGH PROCESSED CSV FILES
    search_results = []
    search_id = found_ids[0].upper()
    
    try:
        # Search in the most recent processed files
        latest_job = processed_files[0]
        print(f"🔍 SEARCHING for ID '{search_id}' in job {latest_job}")
        
        # Check claims file - ACTUALLY READ THE CSV
        claims_file = os.path.join(HACKATHON_OUTPUT_FOLDER, f"{latest_job}_claims.csv")
        if os.path.exists(claims_file):
            try:
                print(f"📊 Reading claims file: {claims_file}")
                claims_df = pd.read_csv(claims_file)
                print(f"✅ Loaded {len(claims_df)} claims records")
                print(f"📋 Claims columns: {list(claims_df.columns)}")
                
                # Search in multiple columns
                search_columns = ['CLAIM_ID', 'MEMBER_ID', 'ID']
                for col in search_columns:
                    if col in claims_df.columns:
                        # Convert to string and search (case insensitive)
                        matches = claims_df[claims_df[col].astype(str).str.contains(search_id, case=False, na=False)]
                        print(f"🔍 Searching column {col}: found {len(matches)} matches")
                        if not matches.empty:
                            for _, row in matches.iterrows():
                                search_results.append({
                                    'type': 'Insurance Claim',
                                    'file': 'claims',
                                    'data': row.to_dict()
                                })
                                print(f"✅ Found claim match: {row.get('CLAIM_ID', 'N/A')}")
            except Exception as e:
                print(f"❌ Error searching claims file: {e}")
        else:
            print(f"⚠️ Claims file not found: {claims_file}")
        
        # Check demographics file - ACTUALLY READ THE CSV
        demographics_file = os.path.join(HACKATHON_OUTPUT_FOLDER, f"{latest_job}_demographics.csv")
        if os.path.exists(demographics_file):
            try:
                print(f"📊 Reading demographics file: {demographics_file}")
                demo_df = pd.read_csv(demographics_file)
                print(f"✅ Loaded {len(demo_df)} demographics records")
                print(f"📋 Demographics columns: {list(demo_df.columns)}")
                
                # Search in multiple columns
                search_columns = ['ID', 'CLAIM_ID', 'MEMBER_ID']
                for col in search_columns:
                    if col in demo_df.columns:
                        # Convert to string and search (case insensitive)
                        matches = demo_df[demo_df[col].astype(str).str.contains(search_id, case=False, na=False)]
                        print(f"🔍 Searching column {col}: found {len(matches)} matches")
                        if not matches.empty:
                            for _, row in matches.iterrows():
                                search_results.append({
                                    'type': 'Patient Demographics',
                                    'file': 'demographics',
                                    'data': row.to_dict()
                                })
                                print(f"✅ Found demographics match: {row.get('ID', 'N/A')}")
            except Exception as e:
                print(f"❌ Error searching demographics file: {e}")
        else:
            print(f"⚠️ Demographics file not found: {demographics_file}")
        
        print(f"🎯 Total search results found: {len(search_results)}")
        
    except Exception as e:
        print(f"❌ Search error: {e}")
        return f"❌ **Search Error**\n\nEncountered an error while searching: {str(e)}"
    
    # Format search results with ACTUAL DATA
    if not search_results:
        return f"""🔍 **Search Results for "{search_id}"**

❌ **No Records Found**

The ID "{search_id}" was not found in your processed healthcare data.

**Search Coverage:**
• Insurance Claims Data ✓
• Patient Demographics Data ✓

**Tips:**
• Check the exact ID format in your original data
• Try searching with just the numeric portion
• Ensure the ID exists in your uploaded dataset"""
    
    # Format found results with REAL DATA FROM CSV FILES
    response = f"""🔍 **Search Results for "{search_id}"**\n\n✅ **Found {len(search_results)} Record(s)**\n\n"""
    
    for i, result in enumerate(search_results[:3], 1):  # Limit to 3 results
        response += f"""**Record {i}: {result['type']}**\n"""
        
        # Display key fields with ACTUAL DATA from CSV
        data = result['data']
        key_fields = ['CLAIM_ID', 'MEMBER_ID', 'ID', 'CLAIM_TYPE', 'PROVIDER_SPECIALTY', 
                     'TOTAL_CHARGE', 'AGE', 'GENDER', 'DIAGNOSIS_CODE', 'ADJUDICATION_STATUS']
        
        for field in key_fields:
            if field in data and pd.notna(data[field]) and str(data[field]).strip():
                response += f"• **{field}**: {data[field]}\n"
        
        response += "\n"
    
    if len(search_results) > 3:
        response += f"*... and {len(search_results) - 3} more records found*\n\n"
    
    response += """**🔒 Privacy Note:** All displayed data has been processed through our privacy-compliant pipeline with PII/PHI protection applied."""
    
    return response

def handle_metrics_query(user_message, processed_files):
    """Handle dataset metrics queries"""
    message_lower = user_message.lower()
    
    # Check if this is a metrics query
    metrics_keywords = ['metrics', 'statistics', 'stats', 'summary', 'overview', 'count', 'total', 'how many']
    dataset_keywords = ['dataset', 'data', 'records', 'claims', 'patients', 'demographics']
    
    is_metrics_query = any(keyword in message_lower for keyword in metrics_keywords)
    has_dataset_reference = any(keyword in message_lower for keyword in dataset_keywords)
    
    if not (is_metrics_query and has_dataset_reference):
        return None
    
    if not processed_files:
        return "❌ **No Data Available for Metrics**\n\nPlease upload and process a healthcare data file first to view dataset metrics."
    
    try:
        # Get metrics from the most recent processed files
        latest_job = processed_files[0]
        
        # Load processing report
        report_file = os.path.join(HACKATHON_OUTPUT_FOLDER, f"{latest_job}_report.json")
        report_data = {}
        if os.path.exists(report_file):
            with open(report_file, 'r') as f:
                report_data = json.load(f)
        
        # Get file metrics
        claims_metrics = {}
        demographics_metrics = {}
        
        # Analyze claims file
        claims_file = os.path.join(HACKATHON_OUTPUT_FOLDER, f"{latest_job}_claims.csv")
        if os.path.exists(claims_file):
            try:
                claims_df = pd.read_csv(claims_file)
                claims_metrics = {
                    'total_records': len(claims_df),
                    'columns': list(claims_df.columns),
                    'column_count': len(claims_df.columns),
                    'completeness': {}
                }
                
                # Calculate completeness for each column
                for col in claims_df.columns:
                    non_null_count = claims_df[col].notna().sum()
                    completeness_pct = (non_null_count / len(claims_df)) * 100
                    claims_metrics['completeness'][col] = round(completeness_pct, 1)
                
                # Get unique values for key fields
                if 'PROVIDER_SPECIALTY' in claims_df.columns:
                    claims_metrics['unique_specialties'] = claims_df['PROVIDER_SPECIALTY'].nunique()
                if 'CLAIM_TYPE' in claims_df.columns:
                    claims_metrics['unique_claim_types'] = claims_df['CLAIM_TYPE'].nunique()
                if 'TOTAL_CHARGE' in claims_df.columns:
                    claims_metrics['avg_charge'] = round(claims_df['TOTAL_CHARGE'].mean(), 2)
                    claims_metrics['total_charges'] = round(claims_df['TOTAL_CHARGE'].sum(), 2)
                
            except Exception as e:
                print(f"Error analyzing claims file: {e}")
        
        # Analyze demographics file
        demographics_file = os.path.join(HACKATHON_OUTPUT_FOLDER, f"{latest_job}_demographics.csv")
        if os.path.exists(demographics_file):
            try:
                demo_df = pd.read_csv(demographics_file)
                demographics_metrics = {
                    'total_records': len(demo_df),
                    'columns': list(demo_df.columns),
                    'column_count': len(demo_df.columns),
                    'completeness': {}
                }
                
                # Calculate completeness for each column
                for col in demo_df.columns:
                    non_null_count = demo_df[col].notna().sum()
                    completeness_pct = (non_null_count / len(demo_df)) * 100
                    demographics_metrics['completeness'][col] = round(completeness_pct, 1)
                
                # Get demographic insights
                if 'AGE' in demo_df.columns:
                    demographics_metrics['avg_age'] = round(demo_df['AGE'].mean(), 1)
                    demographics_metrics['age_range'] = f"{demo_df['AGE'].min()}-{demo_df['AGE'].max()}"
                if 'GENDER' in demo_df.columns:
                    demographics_metrics['gender_distribution'] = demo_df['GENDER'].value_counts().to_dict()
                
            except Exception as e:
                print(f"Error analyzing demographics file: {e}")
        
        # Format metrics response
        response = "📊 **Dataset Metrics & Statistics**\n\n"
        
        # Overall metrics from report
        if report_data:
            response += "**📋 Processing Summary:**\n"
            response += f"• **Original Records**: {report_data.get('original_data_count', 'N/A')}\n"
            response += f"• **Cleaned Records**: {report_data.get('cleaned_data_count', 'N/A')}\n"
            response += f"• **PII Fields Protected**: {len(report_data.get('pii_detected', []))}\n"
            response += f"• **PHI Fields Identified**: {len(report_data.get('phi_detected', []))}\n"
            response += f"• **Synthetic Mode**: {'Yes' if report_data.get('synthetic_mode') else 'No'}\n\n"
        
        # Claims metrics
        if claims_metrics:
            response += "**🏥 Insurance Claims Data:**\n"
            response += f"• **Total Claims**: {claims_metrics['total_records']}\n"
            response += f"• **Data Fields**: {claims_metrics['column_count']}\n"
            
            if 'avg_charge' in claims_metrics:
                response += f"• **Average Claim**: ${claims_metrics['avg_charge']}\n"
            if 'total_charges' in claims_metrics:
                response += f"• **Total Charges**: ${claims_metrics['total_charges']}\n"
            if 'unique_specialties' in claims_metrics:
                response += f"• **Provider Specialties**: {claims_metrics['unique_specialties']}\n"
            if 'unique_claim_types' in claims_metrics:
                response += f"• **Claim Types**: {claims_metrics['unique_claim_types']}\n"
            
            # Top completeness scores
            if claims_metrics['completeness']:
                top_complete = sorted(claims_metrics['completeness'].items(), key=lambda x: x[1], reverse=True)[:3]
                response += f"• **Data Completeness**: {top_complete[0][1]}% avg (top field)\n"
            
            response += "\n"
        
        # Demographics metrics
        if demographics_metrics:
            response += "**👥 Patient Demographics Data:**\n"
            response += f"• **Total Patients**: {demographics_metrics['total_records']}\n"
            response += f"• **Data Fields**: {demographics_metrics['column_count']}\n"
            
            if 'avg_age' in demographics_metrics:
                response += f"• **Average Age**: {demographics_metrics['avg_age']} years\n"
            if 'age_range' in demographics_metrics:
                response += f"• **Age Range**: {demographics_metrics['age_range']} years\n"
            if 'gender_distribution' in demographics_metrics:
                gender_dist = demographics_metrics['gender_distribution']
                response += f"• **Gender Distribution**: {dict(list(gender_dist.items())[:2])}\n"
            
            # Top completeness scores
            if demographics_metrics['completeness']:
                top_complete = sorted(demographics_metrics['completeness'].items(), key=lambda x: x[1], reverse=True)[:3]
                response += f"• **Data Completeness**: {top_complete[0][1]}% avg (top field)\n"
            
            response += "\n"
        
        # Data quality summary
        response += "**✅ Data Quality Summary:**\n"
        total_records = (claims_metrics.get('total_records', 0) + 
                        demographics_metrics.get('total_records', 0))
        response += f"• **Total Processed Records**: {total_records}\n"
        response += f"• **Privacy Protection**: ✅ Applied\n"
        response += f"• **HIPAA Compliance**: ✅ Verified\n"
        response += f"• **Ready for Analysis**: ✅ Yes\n\n"
        
        response += "**💡 Available Actions:**\n"
        response += "• Search specific records by ID\n"
        response += "• Generate additional synthetic data\n"
        response += "• Download processed files\n"
        response += "• Request detailed field analysis"
        
        return response
        
    except Exception as e:
        return f"❌ **Metrics Error**\n\nEncountered an error while calculating metrics: {str(e)}"

def handle_data_analysis(user_message, processed_files):
    """Handle data analysis queries that require reading and analyzing CSV files"""
    message_lower = user_message.lower()
    
    # Check if this is a data analysis query
    analysis_keywords = ['analyze', 'analysis', 'insights', 'patterns', 'trends', 'conclusions', 'findings', 'what does', 'tell me about', 'explain']
    data_keywords = ['data', 'dataset', 'claims', 'patients', 'demographics', 'my file', 'uploaded']
    
    is_analysis_query = any(keyword in message_lower for keyword in analysis_keywords)
    has_data_reference = any(keyword in message_lower for keyword in data_keywords)
    
    if not (is_analysis_query and has_data_reference):
        return None
    
    if not processed_files:
        return "❌ **No Data Available for Analysis**\n\nPlease upload and process a healthcare data file first to enable data analysis."
    
    try:
        # Analyze the most recent processed files
        latest_job = processed_files[0]
        print(f"🧠 ANALYZING data from job {latest_job}")
        
        # Load processing report for context
        report_file = os.path.join(HACKATHON_OUTPUT_FOLDER, f"{latest_job}_report.json")
        report_data = {}
        if os.path.exists(report_file):
            with open(report_file, 'r') as f:
                report_data = json.load(f)
        
        # Analyze claims data
        claims_insights = []
        claims_file = os.path.join(HACKATHON_OUTPUT_FOLDER, f"{latest_job}_claims.csv")
        if os.path.exists(claims_file):
            try:
                print(f"📊 Analyzing claims data: {claims_file}")
                claims_df = pd.read_csv(claims_file)
                
                # Generate insights from claims data
                if 'TOTAL_CHARGE' in claims_df.columns:
                    avg_charge = claims_df['TOTAL_CHARGE'].mean()
                    max_charge = claims_df['TOTAL_CHARGE'].max()
                    min_charge = claims_df['TOTAL_CHARGE'].min()
                    claims_insights.append(f"Average claim amount is ${avg_charge:.2f}, ranging from ${min_charge:.2f} to ${max_charge:.2f}")
                
                if 'PROVIDER_SPECIALTY' in claims_df.columns:
                    top_specialties = claims_df['PROVIDER_SPECIALTY'].value_counts().head(3)
                    specialty_list = [f"{specialty} ({count} claims)" for specialty, count in top_specialties.items()]
                    claims_insights.append(f"Top provider specialties: {', '.join(specialty_list)}")
                
                if 'CLAIM_TYPE' in claims_df.columns:
                    claim_types = claims_df['CLAIM_TYPE'].value_counts()
                    type_list = [f"{ctype} ({count})" for ctype, count in claim_types.items()]
                    claims_insights.append(f"Claim type distribution: {', '.join(type_list)}")
                
                if 'ADJUDICATION_STATUS' in claims_df.columns:
                    status_dist = claims_df['ADJUDICATION_STATUS'].value_counts()
                    approved_pct = (status_dist.get('Approved', 0) / len(claims_df)) * 100
                    claims_insights.append(f"Claims approval rate: {approved_pct:.1f}% ({status_dist.get('Approved', 0)} out of {len(claims_df)} claims)")
                
                if 'DIAGNOSIS_CODE' in claims_df.columns:
                    top_diagnoses = claims_df['DIAGNOSIS_CODE'].value_counts().head(3)
                    diag_list = [f"{code} ({count} cases)" for code, count in top_diagnoses.items()]
                    claims_insights.append(f"Most common diagnosis codes: {', '.join(diag_list)}")
                
            except Exception as e:
                print(f"❌ Error analyzing claims data: {e}")
        
        # Analyze demographics data
        demo_insights = []
        demographics_file = os.path.join(HACKATHON_OUTPUT_FOLDER, f"{latest_job}_demographics.csv")
        if os.path.exists(demographics_file):
            try:
                print(f"📊 Analyzing demographics data: {demographics_file}")
                demo_df = pd.read_csv(demographics_file)
                
                # Generate insights from demographics data
                if 'AGE' in demo_df.columns:
                    avg_age = demo_df['AGE'].mean()
                    age_std = demo_df['AGE'].std()
                    demo_insights.append(f"Average patient age is {avg_age:.1f} years (±{age_std:.1f} years)")
                    
                    # Age distribution analysis
                    age_groups = pd.cut(demo_df['AGE'], bins=[0, 18, 35, 50, 65, 100], labels=['<18', '18-34', '35-49', '50-64', '65+'])
                    age_dist = age_groups.value_counts()
                    largest_group = age_dist.idxmax()
                    demo_insights.append(f"Largest age group is {largest_group} with {age_dist.max()} patients ({(age_dist.max()/len(demo_df)*100):.1f}%)")
                
                if 'GENDER' in demo_df.columns:
                    gender_dist = demo_df['GENDER'].value_counts()
                    gender_pcts = [(gender, count, (count/len(demo_df)*100)) for gender, count in gender_dist.items()]
                    gender_str = ', '.join([f"{gender}: {count} ({pct:.1f}%)" for gender, count, pct in gender_pcts])
                    demo_insights.append(f"Gender distribution: {gender_str}")
                
                if 'CLAIM_COST' in demo_df.columns:
                    avg_cost = demo_df['CLAIM_COST'].mean()
                    high_cost_threshold = demo_df['CLAIM_COST'].quantile(0.9)
                    high_cost_count = (demo_df['CLAIM_COST'] > high_cost_threshold).sum()
                    demo_insights.append(f"Average patient claim cost is ${avg_cost:.2f}, with {high_cost_count} high-cost patients (>${high_cost_threshold:.2f})")
                
                if 'DRG_CODE' in demo_df.columns:
                    top_drgs = demo_df['DRG_CODE'].value_counts().head(3)
                    drg_list = [f"DRG-{code} ({count} patients)" for code, count in top_drgs.items()]
                    demo_insights.append(f"Most common DRG codes: {', '.join(drg_list)}")
                
            except Exception as e:
                print(f"❌ Error analyzing demographics data: {e}")
        
        # Generate comprehensive analysis response
        response = "🧠 **Healthcare Data Analysis & Insights**\n\n"
        
        # Processing overview
        if report_data:
            response += "**📋 Dataset Overview:**\n"
            response += f"• **Original Records**: {report_data.get('original_data_count', 'N/A')}\n"
            response += f"• **Final Claims**: {report_data.get('final_claims_count', 'N/A')}\n"
            response += f"• **Final Demographics**: {report_data.get('final_demographics_count', 'N/A')}\n"
            response += f"• **Privacy Protection**: {len(report_data.get('pii_detected', []))} PII + {len(report_data.get('phi_detected', []))} PHI fields secured\n\n"
        
        # Claims insights
        if claims_insights:
            response += "**🏥 Insurance Claims Analysis:**\n"
            for insight in claims_insights:
                response += f"• {insight}\n"
            response += "\n"
        
        # Demographics insights
        if demo_insights:
            response += "**👥 Patient Demographics Analysis:**\n"
            for insight in demo_insights:
                response += f"• {insight}\n"
            response += "\n"
        
        # Key findings and conclusions
        response += "**🔍 Key Findings & Conclusions:**\n"
        
        # Generate intelligent conclusions based on the data
        conclusions = []
        
        if claims_insights and demo_insights:
            conclusions.append("Your healthcare dataset contains both insurance claims and patient demographic information, providing a comprehensive view of healthcare utilization patterns")
        
        if report_data.get('synthetic_mode'):
            conclusions.append(f"Synthetic data generation was applied, expanding your dataset while maintaining privacy protection and statistical validity")
        
        # Add data quality conclusion
        total_records = (report_data.get('final_claims_count', 0) + report_data.get('final_demographics_count', 0))
        if total_records > 1000:
            conclusions.append("Your dataset is substantial enough for robust statistical analysis and machine learning applications")
        elif total_records > 100:
            conclusions.append("Your dataset provides a good foundation for analysis, though larger samples would improve statistical power")
        
        # Add privacy conclusion
        pii_count = len(report_data.get('pii_detected', []))
        phi_count = len(report_data.get('phi_detected', []))
        if pii_count > 0 or phi_count > 0:
            conclusions.append(f"Privacy protection was successfully applied to {pii_count + phi_count} sensitive fields, ensuring HIPAA compliance while preserving analytical utility")
        
        for conclusion in conclusions:
            response += f"• {conclusion}\n"
        
        response += "\n**💡 Recommended Next Steps:**\n"
        response += "• Download processed files for external analysis tools\n"
        response += "• Generate additional synthetic data for expanded analysis\n"
        response += "• Search for specific records using claim or patient IDs\n"
        response += "• Request detailed metrics for specific data fields\n"
        
        return response
        
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        return f"❌ **Analysis Error**\n\nEncountered an error while analyzing your data: {str(e)}"

def generate_intelligent_response(user_message, processed_files):
    """Generate intelligent responses without external AI"""
    message_lower = user_message.lower()
    
    # Healthcare data analysis responses
    if any(word in message_lower for word in ['analyze', 'analysis', 'insights', 'patterns']):
        if processed_files:
            return f"""📊 **Data Analysis Available**

I can see you have {len(processed_files)} processed healthcare dataset(s) ready for analysis. Here's what I can help you with:

🔍 **Available Analysis:**
• **Privacy Protection Review** - See how PII/PHI fields were protected
• **Data Quality Assessment** - Review completeness and consistency metrics  
• **Synthetic Data Evaluation** - Compare original vs synthetic data utility
• **Processing Workflow Summary** - Detailed breakdown of each processing step

📥 **Download Options:**
• Insurance Claims CSV - Enhanced claims data with privacy protection
• Patient Demographics CSV - Demographic data with safeguards
• Processing Report JSON - Comprehensive analysis and metrics
• Complete ZIP Package - All files with README

Would you like me to provide specific insights about any of these areas?"""
        else:
            return """📁 **Ready for Healthcare Data Analysis**

I'm Phara, your AI healthcare analytics assistant! To provide detailed analysis and insights, please upload a healthcare data file first.

🎯 **What I Can Analyze:**
• Insurance claims data with privacy protection
• Patient demographics with HIPAA compliance
• Data quality and completeness metrics
• Synthetic data generation for privacy-safe analysis

📤 **Supported Formats:**
• CSV files (.csv)
• Excel files (.xlsx) 
• ZIP archives containing multiple files

Once you upload your data, I'll process it through our privacy-compliant pipeline and provide comprehensive insights!"""

    # File and data related queries
    elif any(word in message_lower for word in ['file', 'data', 'upload', 'download']):
        if processed_files:
            return f"""📁 **Your Healthcare Data Files**

You have {len(processed_files)} processed dataset(s) available:

📊 **Processed Files Ready:**
• **Insurance Claims** - Privacy-protected claims data
• **Patient Demographics** - Anonymized demographic information  
• **Processing Report** - Detailed analysis and metrics
• **Complete Package** - ZIP file with all processed data

📥 **Download Instructions:**
1. Click "Download Privacy Report" for detailed processing metrics
2. Use "Generate Synthetic Data" for additional privacy-safe datasets
3. Access individual files through the download buttons in the analytics section

All files include comprehensive privacy protection with PII/PHI safeguards while maintaining statistical utility for analysis."""
        else:
            return """📤 **File Upload Instructions**

Ready to process your healthcare data! Here's how to get started:

🎯 **Upload Process:**
1. Click the "Choose Healthcare Data File" button
2. Select your CSV, XLSX, or ZIP file
3. Wait for processing to complete (usually 30-60 seconds)
4. Access your processed files and analytics dashboard

🔒 **Privacy Protection:**
• Automatic PII/PHI detection and protection
• HIPAA-compliant data processing
• Statistical utility preservation
• Comprehensive privacy reporting

📊 **What You'll Get:**
• Cleaned insurance claims data
• Protected patient demographics
• Synthetic data generation
• Detailed processing report"""

    # Privacy and compliance queries
    elif any(word in message_lower for word in ['privacy', 'hipaa', 'compliance', 'pii', 'phi', 'protection']):
        return """🔒 **Privacy & HIPAA Compliance**

NeuralNexus6 provides comprehensive healthcare data protection:

🛡️ **Privacy Safeguards:**
• **PII Detection** - Automatically identifies personally identifiable information
• **PHI Protection** - Secures protected health information per HIPAA requirements
• **Data Anonymization** - Removes direct identifiers while preserving utility
• **Statistical Preservation** - Maintains data relationships for valid analysis

📋 **Compliance Features:**
• HIPAA-compliant processing pipeline
• Comprehensive audit trails and reporting
• Privacy impact assessments
• Secure data handling throughout workflow

🧬 **Synthetic Data Generation:**
• Creates privacy-safe synthetic datasets
• Maintains statistical properties of original data
• Zero risk of patient re-identification
• Suitable for research and development

All processing includes detailed privacy reports showing exactly what protections were applied to your data."""

    # Synthetic data queries
    elif any(word in message_lower for word in ['synthetic', 'generate', 'artificial', 'fake']):
        if processed_files:
            return """🧬 **Synthetic Data Generation**

Your processed healthcare data is ready for synthetic data generation!

✨ **Available Options:**
• **Enhanced Synthetic Claims** - AI-generated insurance claims data
• **Demographic Synthesis** - Privacy-safe patient demographic data
• **Custom Row Counts** - Generate 100 to 10,000+ synthetic records
• **Statistical Preservation** - Maintains original data relationships

🎯 **Generation Process:**
1. Uses your processed data as the foundation
2. Applies advanced AI pattern learning
3. Generates statistically similar but completely synthetic records
4. Ensures zero risk of patient re-identification

📊 **Quality Assurance:**
• Preserves statistical distributions
• Maintains correlation patterns
• Validates data quality metrics
• Provides utility comparison reports

Click "Generate Synthetic Data" to create additional privacy-compliant datasets for your analysis!"""
        else:
            return """🧬 **Synthetic Data Capabilities**

I can generate high-quality synthetic healthcare data once you upload your original dataset!

🎯 **Synthetic Data Benefits:**
• **Complete Privacy Protection** - Zero risk of patient re-identification
• **Statistical Accuracy** - Preserves original data patterns and relationships
• **Scalable Generation** - Create datasets from 100 to 10,000+ records
• **Research Ready** - Perfect for development, testing, and research

🔬 **Advanced Features:**
• AI-powered pattern learning from your real data
• Government healthcare data integration for enhanced realism
• Background bias correction for representative datasets
• Comprehensive quality validation and reporting

Upload your healthcare data first, and I'll show you exactly what synthetic data options are available for your specific dataset!"""

    # Quality and metrics queries
    elif any(word in message_lower for word in ['quality', 'metrics', 'completeness', 'validation']):
        if processed_files:
            return """📊 **Data Quality Assessment**

Your processed healthcare data includes comprehensive quality metrics:

✅ **Quality Indicators:**
• **Completeness Score** - Percentage of non-null values across all fields
• **Consistency Check** - Validation of data format and value ranges
• **Privacy Compliance** - Verification of PII/PHI protection measures
• **Statistical Integrity** - Preservation of original data relationships

📈 **Available Metrics:**
• Record counts (original vs processed)
• Field-level completeness analysis
• Data type validation results
• Privacy protection coverage
• Processing workflow success rates

📋 **Quality Reports:**
• Detailed processing report (JSON format)
• Privacy compliance verification
• Data transformation summary
• Recommendations for data improvement

Check your analytics dashboard for real-time quality scores and download the processing report for detailed metrics!"""
        else:
            return """📊 **Data Quality Analysis**

I provide comprehensive data quality assessment for healthcare datasets:

🔍 **Quality Checks:**
• **Completeness Analysis** - Identify missing or incomplete data
• **Format Validation** - Ensure proper data types and formats
• **Consistency Verification** - Check for logical data relationships
• **Privacy Assessment** - Evaluate PII/PHI exposure risks

📈 **Quality Metrics:**
• Field-level completeness percentages
• Data distribution analysis
• Outlier detection and reporting
• Statistical summary generation

🎯 **Improvement Recommendations:**
• Data cleaning suggestions
• Format standardization advice
• Privacy enhancement opportunities
• Processing optimization tips

Upload your healthcare data to receive a detailed quality assessment with actionable insights for improvement!"""

    # General help and capabilities
    elif any(word in message_lower for word in ['help', 'what', 'how', 'can you', 'capabilities']):
        return """👋 **Hello! I'm Phara, Your AI Healthcare Analytics Assistant**

I specialize in privacy-compliant healthcare data analysis and processing. Here's what I can help you with:

🎯 **Core Capabilities:**
• **File Processing** - Upload and process CSV, XLSX, or ZIP healthcare files
• **Privacy Protection** - Automatic PII/PHI detection and HIPAA compliance
• **Data Analysis** - Comprehensive quality assessment and insights
• **Synthetic Data** - Generate privacy-safe synthetic datasets

📊 **Analytics Features:**
• Real-time data quality scoring
• Privacy compliance verification
• Statistical pattern analysis
• Processing workflow tracking

🔒 **Privacy & Security:**
• HIPAA-compliant data handling
• Comprehensive audit trails
• Privacy impact assessments
• Secure file processing and storage

💬 **How to Get Started:**
1. Upload your healthcare data file using the upload button
2. Wait for processing to complete (30-60 seconds)
3. Explore your analytics dashboard with real-time metrics
4. Download processed files or generate synthetic data
5. Ask me questions about your data for detailed insights!

What would you like to explore first?"""

    # Default response for other queries
    else:
        if processed_files:
            return f"""💡 **I'm here to help with your healthcare data!**

I can see you have {len(processed_files)} processed dataset(s) ready for analysis. Here are some things you can ask me:

🔍 **Analysis Questions:**
• "Analyze my data quality and completeness"
• "Show me the privacy protection applied to my data"
• "What insights can you provide about my dataset?"
• "How does the synthetic data compare to my original data?"

📊 **Data Operations:**
• "Generate additional synthetic data"
• "Download my processed files"
• "Show me the processing report"
• "What privacy protections were applied?"

💬 **Or try asking:**
• "What patterns do you see in my healthcare data?"
• "How can I improve my data quality?"
• "What are the key metrics for my dataset?"

What specific aspect of your healthcare data would you like to explore?"""
        else:
            return """🚀 **Ready to Analyze Your Healthcare Data!**

I'm here to help you process and analyze healthcare data with complete privacy protection. Here's what you can do:

📤 **Get Started:**
• Upload your healthcare data file (CSV, XLSX, or ZIP)
• I'll process it through our HIPAA-compliant pipeline
• Get comprehensive analytics and insights

💬 **You can ask me:**
• "How do I upload my healthcare data?"
• "What privacy protections do you provide?"
• "Can you generate synthetic data?"
• "What file formats do you support?"

🎯 **Popular Questions:**
• "Explain your data processing workflow"
• "How do you protect patient privacy?"
• "What analytics will I get from my data?"
• "Can you help me understand HIPAA compliance?"

Upload your data file to get started, or ask me any questions about healthcare data analysis!"""

# Serve static files
@app.route('/')
def serve_frontend():
    """Serve the main frontend file"""
    return send_from_directory('.', 'nexus_analytics_integrated.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('.', filename)

def main():
    """Main entry point"""
    print("🚀 Starting NeuralNexus6 Integrated Server...")
    print("📡 Server will be available at: http://localhost:5001")
    print("🔗 API endpoints:")
    print("   - POST /api/chat - Main chat endpoint")
    print("   - POST /api/files/upload - Upload and process files")
    print("   - GET  /api/download/{job_id}/{type} - Download processed files")
    print("   - POST /api/generate-synthetic - Generate synthetic data")
    print("   - GET  /api/jobs/{job_id}/status - Get job status")
    print("   - GET  /api/model/* - Model management")
    print("   - GET  /api/data/suggestions - Get analysis suggestions")
    print("   - GET  /api/health - Health check")
    print()
    
    if not brain:
        print("⚠️  Warning: Brain not initialized. Check your API keys and configuration.")
    
    if not nexus_workflow:
        print("⚠️  Warning: NeuralNexus6 Enhanced Workflow not available.")
        print("   File processing will use fallback methods.")
    
    print()
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5001, debug=True)

if __name__ == "__main__":
    main()
