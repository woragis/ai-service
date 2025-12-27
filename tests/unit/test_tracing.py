"""
Unit tests for tracing functionality.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from opentelemetry import trace


class TestTracing:
    """Tests for tracing module."""

    def test_get_trace_id_no_context(self):
        """Test getting trace ID when no context exists."""
        from app.tracing import get_trace_id
        
        # Mock no current span
        with patch('app.tracing.trace.get_current_span', return_value=None):
            result = get_trace_id()
            assert result is None

    def test_get_trace_id_with_context(self):
        """Test getting trace ID from current span."""
        from app.tracing import get_trace_id
        
        # Mock current span with valid context
        mock_span = Mock()
        mock_span_context = Mock()
        mock_span_context.is_valid = True
        mock_span_context.trace_id = 0x1234567890abcdef1234567890abcdef
        mock_span.get_span_context.return_value = mock_span_context
        
        with patch('app.tracing.trace.get_current_span', return_value=mock_span):
            result = get_trace_id()
            assert result is not None
            assert isinstance(result, str)

    def test_get_trace_id_from_context_var(self):
        """Test getting trace ID from context variable."""
        from app.tracing import get_trace_id, set_trace_id
        
        # Set trace ID in context variable
        set_trace_id("test-trace-id-123")
        
        # Mock no current span
        with patch('app.tracing.trace.get_current_span', return_value=None):
            result = get_trace_id()
            assert result == "test-trace-id-123"

    def test_set_trace_id(self):
        """Test setting trace ID."""
        from app.tracing import set_trace_id, get_trace_id
        
        set_trace_id("test-trace-456")
        
        # Mock no current span to use context variable
        with patch('app.tracing.trace.get_current_span', return_value=None):
            result = get_trace_id()
            assert result == "test-trace-456"

    def test_get_tracer_not_initialized(self):
        """Test getting tracer when not initialized."""
        from app.tracing import get_tracer
        
        # Reset global state
        import app.tracing
        app.tracing._tracer = None
        
        tracer = get_tracer()
        # Should return NoOpTracer when not initialized
        assert tracer is not None

    @patch('app.tracing.OTLPSpanExporter')
    @patch('app.tracing.TracerProvider')
    @patch('app.tracing.trace.set_tracer_provider')
    @patch('app.tracing.trace.get_tracer')
    @patch('app.tracing.FastAPIInstrumentor')
    @patch('app.tracing.RequestsInstrumentor')
    def test_init_tracing_success(self, mock_requests_instr, mock_fastapi_instr, 
                                   mock_get_tracer, mock_set_provider, 
                                   mock_tracer_provider, mock_exporter):
        """Test successful tracing initialization."""
        from app.tracing import init_tracing
        
        # Reset global state first
        import app.tracing
        app.tracing._tracer_provider = None
        app.tracing._tracer = None
        
        mock_provider = Mock()
        mock_tracer_provider.return_value = mock_provider
        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer
        
        # Mock the instrumentors
        mock_fastapi_instr_instance = Mock()
        mock_requests_instr_instance = Mock()
        mock_fastapi_instr.return_value = mock_fastapi_instr_instance
        mock_requests_instr.return_value = mock_requests_instr_instance
        
        init_tracing("test-service", "1.0.0", "development")
        
        mock_tracer_provider.assert_called_once()
        mock_set_provider.assert_called_once()

    @patch('app.tracing.OTLPSpanExporter')
    @patch('app.tracing.TracerProvider')
    @patch('app.tracing.trace.set_tracer_provider')
    @patch('app.tracing.trace.get_tracer')
    @patch('app.tracing.FastAPIInstrumentor')
    @patch('app.tracing.RequestsInstrumentor')
    def test_init_tracing_instrumentation_error(self, mock_requests_instr, mock_fastapi_instr,
                                                 mock_get_tracer, mock_set_provider,
                                                 mock_tracer_provider, mock_exporter):
        """Test tracing initialization with instrumentation error."""
        from app.tracing import init_tracing
        
        # Reset global state first
        import app.tracing
        app.tracing._tracer_provider = None
        app.tracing._tracer = None
        
        mock_provider = Mock()
        mock_tracer_provider.return_value = mock_provider
        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer
        
        # Mock the instrumentors to raise exceptions
        mock_fastapi_instr_instance = Mock()
        mock_fastapi_instr_instance.instrument.side_effect = Exception("Instrumentation failed")
        mock_requests_instr_instance = Mock()
        mock_requests_instr_instance.instrument.side_effect = Exception("Instrumentation failed")
        mock_fastapi_instr.return_value = mock_fastapi_instr_instance
        mock_requests_instr.return_value = mock_requests_instr_instance
        
        # Should not raise, just print warning
        init_tracing("test-service", "1.0.0", "development")
        
        # Should still initialize
        mock_tracer_provider.assert_called_once()

    def test_init_tracing_already_initialized(self):
        """Test that init_tracing returns early if already initialized."""
        from app.tracing import init_tracing
        
        # Set up as if already initialized
        import app.tracing
        app.tracing._tracer_provider = Mock()
        
        # Should return early without creating new provider
        with patch('app.tracing.TracerProvider') as mock_provider:
            init_tracing("test-service", "1.0.0", "development")
            mock_provider.assert_not_called()

    def test_shutdown(self):
        """Test tracing shutdown."""
        from app.tracing import shutdown
        
        # Set up provider
        import app.tracing
        mock_provider = Mock()
        app.tracing._tracer_provider = mock_provider
        
        shutdown()
        
        mock_provider.shutdown.assert_called_once()
        assert app.tracing._tracer_provider is None

    @patch('app.tracing.OTLPSpanExporter')
    @patch('app.tracing.TracerProvider')
    @patch('app.tracing.trace.set_tracer_provider')
    @patch('app.tracing.trace.get_tracer')
    @patch('app.tracing.FastAPIInstrumentor')
    @patch('app.tracing.RequestsInstrumentor')
    def test_init_tracing_production(self, mock_requests_instr, mock_fastapi_instr,
                                      mock_get_tracer, mock_set_provider,
                                      mock_tracer_provider, mock_exporter):
        """Test tracing initialization with production environment."""
        from app.tracing import init_tracing
        
        mock_provider = Mock()
        mock_tracer_provider.return_value = mock_provider
        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer
        
        init_tracing("test-service", "1.0.0", "production")
        
        # Should set sampling rate to 0.1 for production
        mock_tracer_provider.assert_called_once()

    @patch('app.tracing.OTLPSpanExporter')
    @patch('app.tracing.TracerProvider')
    @patch('app.tracing.trace.set_tracer_provider')
    @patch('app.tracing.trace.get_tracer')
    @patch('app.tracing.FastAPIInstrumentor')
    @patch('app.tracing.RequestsInstrumentor')
    def test_init_tracing_instrumentation_exception(self, mock_requests_instr, mock_fastapi_instr,
                                                     mock_get_tracer, mock_set_provider,
                                                     mock_tracer_provider, mock_exporter):
        """Test tracing initialization with instrumentation exception."""
        from app.tracing import init_tracing
        
        # Reset global state first
        import app.tracing
        app.tracing._tracer_provider = None
        app.tracing._tracer = None
        
        mock_provider = Mock()
        mock_tracer_provider.return_value = mock_provider
        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer
        
        # Mock the instrumentors to raise exceptions
        mock_fastapi_instr_instance = Mock()
        mock_fastapi_instr_instance.instrument.side_effect = Exception("Instrumentation failed")
        mock_requests_instr_instance = Mock()
        mock_requests_instr_instance.instrument.side_effect = Exception("Instrumentation failed")
        mock_fastapi_instr.return_value = mock_fastapi_instr_instance
        mock_requests_instr.return_value = mock_requests_instr_instance
        
        # Should not raise, just print warning
        init_tracing("test-service", "1.0.0", "development")
        
        # Should still initialize
        mock_tracer_provider.assert_called_once()

    @patch('app.tracing.OTLPSpanExporter')
    @patch('app.tracing.TracerProvider')
    @patch('app.tracing.trace.set_tracer_provider')
    @patch('app.tracing.trace.get_tracer')
    @patch('app.tracing.FastAPIInstrumentor')
    @patch('app.tracing.RequestsInstrumentor')
    def test_get_tracer_initialized(self, mock_requests_instr, mock_fastapi_instr,
                                     mock_get_tracer, mock_set_provider,
                                     mock_tracer_provider, mock_exporter):
        """Test getting tracer when initialized."""
        from app.tracing import init_tracing, get_tracer
        
        # Reset global state first
        import app.tracing
        app.tracing._tracer_provider = None
        app.tracing._tracer = None
        
        mock_provider = Mock()
        mock_tracer_provider.return_value = mock_provider
        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer
        
        # Mock the instrumentors
        mock_fastapi_instr_instance = Mock()
        mock_requests_instr_instance = Mock()
        mock_fastapi_instr.return_value = mock_fastapi_instr_instance
        mock_requests_instr.return_value = mock_requests_instr_instance
        
        init_tracing("test-service", "1.0.0", "development")
        
        # Set the tracer in the module
        app.tracing._tracer = mock_tracer
        
        tracer = get_tracer()
        assert tracer is not None
        assert tracer == mock_tracer

