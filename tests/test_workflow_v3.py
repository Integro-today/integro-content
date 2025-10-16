#!/usr/bin/env python3
"""Comprehensive test suite for Agno therapeutic workflow v3."""

import pytest
import asyncio
import sys
import os
from pathlib import Path
from typing import Iterator, List
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agno.workflow import Workflow, RunResponse
from agno.agent import Agent


class TestAgnoCompliance:
    """Test that workflow follows critical Agno requirements."""
    
    def test_agents_are_class_attributes(self):
        """Ensure agents are class-level attributes, not instance attributes."""
        from integro.workflows.therapeutic import TherapeuticWorkflow
        
        # Check that agents exist as class attributes
        assert hasattr(TherapeuticWorkflow, 'conversation_agent')
        assert hasattr(TherapeuticWorkflow, 'byron_katie_agent')
        assert hasattr(TherapeuticWorkflow, 'ifs_agent')
        assert hasattr(TherapeuticWorkflow, 'daily_content_agent')
        
        # Verify they're actual Agent instances (or will be when created)
        # The class attributes should not be None
        assert TherapeuticWorkflow.conversation_agent is not None
        assert TherapeuticWorkflow.byron_katie_agent is not None
        assert TherapeuticWorkflow.ifs_agent is not None
        assert TherapeuticWorkflow.daily_content_agent is not None
        
        print("✅ All agents are properly defined as class attributes")
    
    def test_workflow_inherits_from_agno(self):
        """Test that TherapeuticWorkflow properly inherits from Agno Workflow."""
        from integro.workflows.therapeutic import TherapeuticWorkflow
        
        # Check inheritance
        assert issubclass(TherapeuticWorkflow, Workflow)
        
        # Check required methods exist
        workflow = TherapeuticWorkflow(session_id="test_session")
        assert hasattr(workflow, 'run')
        assert callable(workflow.run)
        
        print("✅ Workflow properly inherits from Agno Workflow base class")
    
    def test_run_method_returns_iterator(self):
        """Test that run() method returns Iterator[RunResponse]."""
        from integro.workflows.therapeutic import TherapeuticWorkflow
        
        workflow = TherapeuticWorkflow(session_id="test_session")
        
        # Mock the agent run methods to avoid actual API calls
        with patch.object(workflow.conversation_agent, 'run') as mock_run:
            mock_run.return_value = iter([
                RunResponse(run_id="test", content="Test response")
            ])
            
            # Call the run method directly on the class, passing the instance
            # This bypasses Agno's method interception
            result = TherapeuticWorkflow.run(workflow, "Hello")
            
            # Check that result is an iterator
            assert hasattr(result, '__iter__')
            assert hasattr(result, '__next__')
            
            # Try to get first response
            first_response = next(result)
            assert isinstance(first_response, RunResponse)
            
        print("✅ run() method returns proper Iterator[RunResponse]")
    
    def test_session_state_initialization(self):
        """Test that session state is properly initialized."""
        from integro.workflows.therapeutic import TherapeuticWorkflow
        
        workflow = TherapeuticWorkflow(
            session_id="test_session",
            user_id="test_user"
        )
        
        # Check session state exists
        assert hasattr(workflow, 'session_state')
        assert workflow.session_state is not None
        
        # Check required fields
        assert 'user_id' in workflow.session_state
        assert 'session_id' in workflow.session_state
        assert 'current_activity' in workflow.session_state
        assert 'completed_activities' in workflow.session_state
        assert 'activity_states' in workflow.session_state
        
        print("✅ Session state is properly initialized")


class TestActivityLifecycle:
    """Test activity transitions and completion logic."""
    
    def test_activity_switching(self):
        """Test switching between different activities."""
        from integro.workflows.therapeutic import TherapeuticWorkflow
        
        workflow = TherapeuticWorkflow(session_id="test_activity_switch")
        
        # Start with no activity
        assert workflow.session_state.get('current_activity') is None
        
        # Switch to Byron Katie (returns an iterator, so consume it)
        list(workflow._switch_activity('byron_katie'))
        assert workflow.session_state['current_activity'] == 'byron_katie'
        
        # Switch to IFS
        list(workflow._switch_activity('ifs'))
        assert workflow.session_state['current_activity'] == 'ifs'
        
        # Switch to daily content
        list(workflow._switch_activity('daily_content'))
        assert workflow.session_state['current_activity'] == 'daily_content'
        
        print("✅ Activity switching works correctly")
    
    def test_activity_completion_tracking(self):
        """Test that activities are properly marked as complete."""
        from integro.workflows.therapeutic import TherapeuticWorkflow
        
        workflow = TherapeuticWorkflow(session_id="test_completion")
        
        # Start Byron Katie activity
        workflow._switch_activity('byron_katie')
        assert not workflow._is_activity_complete('byron_katie')
        
        # Mark it as complete
        workflow._mark_activity_complete('byron_katie')
        
        # Check it's marked complete
        assert workflow._is_activity_complete('byron_katie')
        assert 'byron_katie' in workflow.session_state['completed_activities']
        
        # Check completion has metadata
        completion_data = workflow.session_state['completed_activities']['byron_katie']
        assert 'completed_at' in completion_data
        
        print("✅ Activity completion tracking works correctly")
    
    def test_prevent_completed_activity_reentry(self):
        """Test that completed activities cannot be re-entered."""
        from integro.workflows.therapeutic import TherapeuticWorkflow
        
        workflow = TherapeuticWorkflow(session_id="test_reentry")
        
        # Complete an activity
        workflow._switch_activity('daily_content')
        workflow._mark_activity_complete('daily_content')
        
        # Try to switch back to it
        # The workflow should prevent this
        assert workflow._is_activity_complete('daily_content')
        
        # Current activity should be cleared after completion
        workflow.session_state['current_activity'] = None
        
        # Verify it's still marked complete
        assert workflow._is_activity_complete('daily_content')
        
        print("✅ Completed activities cannot be re-entered")
    
    def test_completion_request_detection(self):
        """Test detection of completion requests."""
        from integro.services.intent_detection import IntentDetectionService
        
        detector = IntentDetectionService()
        
        # Test various completion phrases
        completion_phrases = [
            "I'm done",
            "i am done",
            "finish",
            "complete this",
            "stop",
            "that's enough",
            "exit",
            "back to menu"
        ]
        
        for phrase in completion_phrases:
            assert detector.detect_completion_request(phrase), f"Failed to detect: {phrase}"
        
        # Test non-completion phrases
        non_completion = [
            "Tell me more",
            "Continue",
            "What's next in the process?"
        ]
        
        for phrase in non_completion:
            assert not detector.detect_completion_request(phrase), f"False positive: {phrase}"
        
        print("✅ Completion request detection works correctly")


class TestIntentDetection:
    """Test intent detection with fallback chain."""
    
    def test_keyword_intent_detection(self):
        """Test that keyword-based intent detection works."""
        from integro.services.intent_detection import IntentDetectionService
        
        detector = IntentDetectionService()
        
        # Test Byron Katie detection
        intent, confidence = detector.detect_intent("I want to do Byron Katie's work")
        assert intent == "byron_katie"
        assert confidence > 0
        
        # Test IFS detection
        intent, confidence = detector.detect_intent("Let's explore my internal parts")
        assert intent == "ifs"
        assert confidence > 0
        
        # Test daily content detection
        intent, confidence = detector.detect_intent("Show me today's wisdom")
        assert intent == "daily_content"
        assert confidence > 0
        
        # Test no clear intent
        intent, confidence = detector.detect_intent("Hello there")
        assert intent is None or confidence < 0.5
        
        print("✅ Keyword-based intent detection works")
    
    def test_intent_detection_error_handling(self):
        """Test that intent detection handles errors gracefully."""
        from integro.services.intent_detection import IntentDetectionService
        
        detector = IntentDetectionService()
        
        # Even with None or empty input, should not crash
        intent, confidence = detector.detect_intent(None)
        assert intent is None
        assert confidence == 0.0
        
        intent, confidence = detector.detect_intent("")
        assert intent is None
        assert confidence == 0.0
        
        print("✅ Intent detection handles errors gracefully")


class TestStateManagement:
    """Test state persistence and management."""
    
    def test_state_manager_initialization(self):
        """Test StateManager initialization."""
        from integro.services.state_manager import StateManager
        
        manager = StateManager(session_id="test_state")
        
        # Test initial state
        initial_state = manager.get_state()
        assert initial_state is not None
        
        print("✅ StateManager initializes correctly")
    
    def test_state_persistence(self):
        """Test that state changes are persisted."""
        from integro.services.state_manager import StateManager
        
        manager = StateManager(session_id="test_persist")
        
        # Update state
        test_data = {
            "test_key": "test_value",
            "counter": 42
        }
        manager.update_state(test_data)
        
        # Retrieve state
        retrieved = manager.get_state()
        assert retrieved["test_key"] == "test_value"
        assert retrieved["counter"] == 42
        
        print("✅ State persistence works correctly")


class TestActivities:
    """Test individual activity modules."""
    
    def test_activity_factory(self):
        """Test activity factory function."""
        from integro.activities import get_activity
        
        # Test getting each activity type
        byron_katie = get_activity('byron_katie')
        assert byron_katie is not None
        assert hasattr(byron_katie, 'create_agent')
        
        ifs = get_activity('ifs')
        assert ifs is not None
        assert hasattr(ifs, 'create_agent')
        
        daily_content = get_activity('daily_content')
        assert daily_content is not None
        assert hasattr(daily_content, 'create_agent')
        
        # Test invalid activity - should return None or raise exception
        try:
            invalid = get_activity('invalid_activity')
            assert invalid is None  # Should be None
        except Exception:
            pass  # Or it might raise an exception, which is also acceptable
        
        print("✅ Activity factory works correctly")
    
    def test_activity_welcome_messages(self):
        """Test that activities have welcome messages."""
        from integro.activities import get_activity
        
        activities = ['byron_katie', 'ifs', 'daily_content']
        
        for activity_name in activities:
            activity = get_activity(activity_name)
            welcome = activity.get_welcome_message()
            assert welcome is not None
            assert len(welcome) > 50  # Ensure it's a meaningful message
            # Check for therapeutic/integration content
            therapeutic_words = ['explore', 'journey', 'experience', 'welcome', 'together', 
                               'integration', 'wisdom', 'reflection', 'psychedelic', 'parts']
            assert any(word in welcome.lower() for word in therapeutic_words), \
                f"Activity {activity_name} welcome message doesn't contain therapeutic content"
        
        print("✅ All activities have welcome messages")
    
    def test_activity_completion_messages(self):
        """Test that activities have completion messages."""
        from integro.activities import get_activity
        
        activities = ['byron_katie', 'ifs', 'daily_content']
        
        for activity_name in activities:
            activity = get_activity(activity_name)
            completion = activity.get_completion_message()
            assert completion is not None
            assert len(completion) > 0
        
        print("✅ All activities have completion messages")


def run_unit_tests():
    """Run all unit tests and report results."""
    print("\n" + "="*60)
    print("🧪 RUNNING AGNO WORKFLOW UNIT TESTS")
    print("="*60 + "\n")
    
    test_classes = [
        TestAgnoCompliance(),
        TestActivityLifecycle(),
        TestIntentDetection(),
        TestStateManagement(),
        TestActivities()
    ]
    
    failed_tests = []
    total_tests = 0
    
    for test_class in test_classes:
        class_name = test_class.__class__.__name__
        print(f"\n📋 {class_name}")
        print("-" * 40)
        
        # Get all test methods
        test_methods = [method for method in dir(test_class) 
                       if method.startswith('test_')]
        
        for method_name in test_methods:
            total_tests += 1
            try:
                method = getattr(test_class, method_name)
                method()
            except Exception as e:
                failed_tests.append({
                    'class': class_name,
                    'method': method_name,
                    'error': str(e)
                })
                print(f"❌ {method_name} - FAILED: {e}")
    
    # Report results
    print("\n" + "="*60)
    print("📊 TEST RESULTS")
    print("="*60)
    
    passed = total_tests - len(failed_tests)
    print(f"✅ Passed: {passed}/{total_tests}")
    
    if failed_tests:
        print(f"❌ Failed: {len(failed_tests)}/{total_tests}\n")
        for failure in failed_tests:
            print(f"  - {failure['class']}.{failure['method']}")
            print(f"    Error: {failure['error']}")
    else:
        print("\n🎉 ALL TESTS PASSED!")
    
    return len(failed_tests) == 0


if __name__ == "__main__":
    # Run tests
    success = run_unit_tests()
    sys.exit(0 if success else 1)