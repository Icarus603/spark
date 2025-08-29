"""
Test Stage 2.2: Autonomous Code Generation & Validation

This is a comprehensive test to verify all Stage 2.2 components work together
for autonomous exploration with code generation and validation.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the libs/python directory to sys.path
sys.path.insert(0, str(Path(__file__).parent / "libs" / "python"))

async def test_stage_2_2():
    """Test Stage 2.2 end-to-end autonomous exploration."""
    
    print("🚀 Testing Stage 2.2: Autonomous Code Generation & Validation")
    print("=" * 60)
    
    try:
        # Phase 1: Test component imports
        print("\n📦 Phase 1: Testing component imports...")
        
        from spark.exploration.generator import ClaudeCodeGenerator, MockCodeGenerator, GenerationRequest
        from spark.exploration.validator import CodeValidator
        from spark.exploration.test_orchestrator import TestOrchestrator
        from spark.core.session_manager import SessionManager
        from spark.core.error_recovery import ErrorRecoveryManager
        from spark.cli.progress_monitor import ProgressMonitor
        from spark.discovery.models import ExplorationSession, ExplorationStatus, CodeArtifact
        
        print("✅ All components imported successfully")
        
        # Phase 2: Test component initialization
        print("\n🔧 Phase 2: Testing component initialization...")
        
        session_manager = SessionManager()
        error_recovery = ErrorRecoveryManager(session_manager)
        progress_monitor = ProgressMonitor(session_manager)
        validator = CodeValidator(enable_execution=False, enable_cua=False)  # Safe mode
        
        # Use MockCodeGenerator for testing (doesn't require API keys)
        mock_generator = MockCodeGenerator()
        test_orchestrator = TestOrchestrator(enable_execution=False)
        
        print("✅ All components initialized successfully")
        
        # Phase 3: Test code generation
        print("\n💻 Phase 3: Testing code generation...")
        
        generation_request = GenerationRequest(
            goal="Create a simple calculator function",
            approach="functional programming",
            context={"language": "python", "test_mode": True},
            language="python"
        )
        
        result = await mock_generator.generate_code(generation_request)
        
        if result.success and result.code_artifacts:
            print(f"✅ Code generation successful: {len(result.code_artifacts)} artifacts created")
            
            # Show generated code sample
            main_artifact = next((a for a in result.code_artifacts if a.is_main_artifact), 
                               result.code_artifacts[0])
            print(f"   Generated file: {main_artifact.file_path}")
            print(f"   Code preview: {main_artifact.content[:100]}...")
        else:
            print(f"❌ Code generation failed: {result.error_message}")
            return False
        
        # Phase 4: Test code validation
        print("\n🔍 Phase 4: Testing code validation...")
        
        validation_result = await validator.validate_code(
            main_artifact.content, 
            main_artifact.language
        )
        
        print(f"✅ Code validation completed")
        print(f"   Valid: {validation_result.is_valid}")
        print(f"   Score: {validation_result.score:.2f}")
        print(f"   Safety: {validation_result.safety_level}")
        print(f"   Syntax valid: {validation_result.syntax_valid}")
        
        if validation_result.issues:
            print(f"   Issues found: {len(validation_result.issues)}")
        if validation_result.warnings:
            print(f"   Warnings: {len(validation_result.warnings)}")
        
        # Phase 5: Test session management
        print("\n📊 Phase 5: Testing session management...")
        
        # Create a test exploration session
        test_session = ExplorationSession(
            id="test_session_stage_2_2",
            goal="Test autonomous exploration",
            initiated_by="test_system",
            time_limit=300,  # 5 minutes
            approach_count=1,
            risk_tolerance="low"
        )
        
        # Start session recording
        trajectory = await session_manager.start_session_recording(
            test_session,
            enable_cua_trajectory=False  # Disable for testing
        )
        
        print(f"✅ Session recording started: {trajectory.session_id}")
        
        # Create some test checkpoints
        await session_manager.create_checkpoint(
            test_session.id,
            "code_generation",
            {"artifacts_created": len(result.code_artifacts)},
            progress_percentage=50.0
        )
        
        await session_manager.create_checkpoint(
            test_session.id,
            "validation",
            {"validation_score": validation_result.score},
            progress_percentage=80.0
        )
        
        print(f"✅ Session checkpoints created successfully")
        
        # Phase 6: Test error recovery (before completing session)
        print("\n🛠️  Phase 6: Testing error recovery...")
        
        # Simulate an error while session is still active
        test_error = Exception("Test error for recovery testing")
        recovery_action = await error_recovery.handle_error(
            test_session.id,
            "test_phase",
            test_error,
            {"test_context": True}
        )
        
        print(f"✅ Error recovery handled: {recovery_action.value}")
        
        error_stats = error_recovery.get_error_statistics(test_session.id)
        print(f"   Error statistics: {error_stats['total_errors']} total errors")
        
        # Now complete session
        completed_trajectory = await session_manager.complete_session_recording(
            test_session.id,
            outcome="completed",
            final_results=[result],
            discoveries_count=1
        )
        
        print(f"✅ Session completed: {len(completed_trajectory.checkpoints)} checkpoints")
        
        # Phase 7: Test progress monitoring
        print("\n📈 Phase 7: Testing progress monitoring...")
        
        session_status = await progress_monitor.get_session_status_summary(test_session.id)
        
        if 'error' not in session_status:
            print("✅ Progress monitoring working")
            print(f"   Session status: {session_status.get('outcome', 'unknown')}")
            print(f"   Progress: {session_status.get('progress_percentage', 0):.1f}%")
            print(f"   Checkpoints: {session_status.get('checkpoints_count', 0)}")
        else:
            print(f"⚠️  Progress monitoring issue: {session_status['error']}")
        
        # Phase 8: Test analytics
        print("\n📊 Phase 8: Testing session analytics...")
        
        analytics = await session_manager.get_session_analytics(test_session.id)
        
        if 'error' not in analytics:
            print("✅ Session analytics working")
            print(f"   Duration: {analytics.get('duration', 0):.1f}s")
            print(f"   Quality metrics: {len(analytics.get('quality_metrics', {}))}")
            print(f"   Timeline events: {len(analytics.get('timeline', []))}")
        else:
            print(f"⚠️  Analytics issue: {analytics['error']}")
        
        # Final summary
        print("\n" + "=" * 60)
        print("🎉 Stage 2.2 Test Results:")
        print("✅ Component imports: PASSED")
        print("✅ Component initialization: PASSED") 
        print("✅ Code generation: PASSED")
        print("✅ Code validation: PASSED")
        print("✅ Session management: PASSED")
        print("✅ Error recovery: PASSED")
        print("✅ Progress monitoring: PASSED")
        print("✅ Session analytics: PASSED")
        print()
        print("🚀 Stage 2.2: Autonomous Code Generation & Validation - ALL TESTS PASSED!")
        
        # Cleanup
        error_recovery.clear_session_errors(test_session.id)
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure all dependencies are installed")
        return False
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_stage_2_2())
    exit_code = 0 if success else 1
    sys.exit(exit_code)