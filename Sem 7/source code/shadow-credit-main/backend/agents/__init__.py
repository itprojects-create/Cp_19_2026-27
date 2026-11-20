from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import asyncio
import time
import uuid
from datetime import datetime, timezone


@dataclass
class AgentOutput:
    agent_id: str
    agent_name: str
    session_id: str
    success: bool
    data: dict
    confidence_score: float          # 0.0 to 1.0
    latency_ms: int
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    fallback_used: bool = False      # True if primary method failed

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "session_id": self.session_id,
            "success": self.success,
            "data": self.data,
            "confidence_score": self.confidence_score,
            "latency_ms": self.latency_ms,
            "errors": self.errors,
            "warnings": self.warnings,
            "fallback_used": self.fallback_used
        }


class BaseAgent(ABC):
    """Abstract base class for all Shadow Credit agents.
    
    Class-level attributes to override in each subclass:
        agent_id: str      e.g. "AGENT_01_OCR"
        name: str          e.g. "OCR Ingestion Agent"
        version: str       e.g. "1.0.0"
    """
    agent_id: str
    name: str
    version: str = "1.0.0"

    def __init__(self, audit_logger, event_bus, settings):
        """
        audit_logger: AuditLogger instance
        event_bus: EventBus instance
        settings: Settings instance from get_settings()
        """
        self.audit_logger = audit_logger
        self.event_bus = event_bus
        self.settings = settings

    @abstractmethod
    async def execute(self, session_id: str, inputs: dict) -> AgentOutput:
        """Subclasses implement ONLY this method.
        
        Contract:
        - MUST return AgentOutput (never raise — catch all exceptions internally)
        - MUST set confidence_score between 0.0 and 1.0
        - MUST set latency_ms
        - If a recoverable error occurs: set success=False, add to errors list,
          set confidence_score=0.0, still return AgentOutput
        """
        pass

    async def run(self, db, session_id: str, inputs: dict) -> AgentOutput:
        """
        ═══════════════════════════════════════════════════
        DO NOT OVERRIDE THIS METHOD IN SUBCLASSES.
        ═══════════════════════════════════════════════════
        
        This is the production safety wrapper. It:
        1. Records start time with time.perf_counter() (high-resolution timer)
        2. Publishes AGENT_STARTED event via event_bus
        3. Logs AGENT_STARTED to audit_log with input hash
        4. Calls self.execute(session_id, inputs) inside try/except Exception
        5. Computes latency_ms from perf_counter delta
        6. On SUCCESS:
           - Publishes AGENT_COMPLETE event with confidence and latency
           - Logs AGENT_COMPLETE to audit_log
           - Returns the AgentOutput from execute()
        7. On EXCEPTION (ANY exception from execute()):
           - Publishes AGENT_ERROR event with error message
           - Logs AGENT_ERROR to audit_log
           - Returns AgentOutput(success=False, errors=[str(exception)], 
             confidence_score=0.0, latency_ms=computed_ms, data={})
           - NEVER re-raises — agent errors must not crash the supervisor
        8. Returns AgentOutput in all cases
        
        This guarantees: any single agent failing cannot crash the pipeline.
        The Supervisor receives AgentOutput regardless of what happened inside.
        """
        start_time = time.perf_counter()
        
        # Publish AGENT_STARTED event
        await self.event_bus.publish({
            "event_type": "AGENT_STARTED",
            "agent_id": self.agent_id,
            "agent_name": self.name,
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Log AGENT_STARTED to audit log
        await self.audit_logger.log(
            db=db,
            session_id=session_id,
            event_type="AGENT_STARTED",
            agent_id=self.agent_id,
            details={"inputs_hash": hash(str(inputs))}
        )
        
        try:
            # Call the subclass implementation
            output = await self.execute(session_id, inputs)
            
            # Compute latency
            end_time = time.perf_counter()
            latency_ms = int((end_time - start_time) * 1000)
            output.latency_ms = latency_ms
            
            # Publish AGENT_COMPLETE event
            await self.event_bus.publish({
                "event_type": "AGENT_COMPLETE",
                "agent_id": self.agent_id,
                "agent_name": self.name,
                "session_id": session_id,
                "success": output.success,
                "confidence_score": output.confidence_score,
                "latency_ms": latency_ms,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            # Log AGENT_COMPLETE to audit log
            await self.audit_logger.log(
                db=db,
                session_id=session_id,
                event_type="AGENT_COMPLETE",
                agent_id=self.agent_id,
                details={
                    "success": output.success,
                    "confidence_score": output.confidence_score,
                    "latency_ms": latency_ms,
                    "fallback_used": output.fallback_used
                }
            )
            
            return output
            
        except Exception as e:
            # Compute latency even on failure
            end_time = time.perf_counter()
            latency_ms = int((end_time - start_time) * 1000)
            
            error_message = str(e)
            
            # Publish AGENT_ERROR event
            await self.event_bus.publish({
                "event_type": "AGENT_ERROR",
                "agent_id": self.agent_id,
                "agent_name": self.name,
                "session_id": session_id,
                "error": error_message,
                "latency_ms": latency_ms,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            # Log AGENT_ERROR to audit log
            await self.audit_logger.log(
                db=db,
                session_id=session_id,
                event_type="AGENT_ERROR",
                agent_id=self.agent_id,
                details={
                    "error": error_message,
                    "latency_ms": latency_ms
                }
            )
            
            # Return failure AgentOutput — NEVER re-raise
            return AgentOutput(
                agent_id=self.agent_id,
                agent_name=self.name,
                session_id=session_id,
                success=False,
                data={},
                confidence_score=0.0,
                latency_ms=latency_ms,
                errors=[error_message],
                warnings=[],
                fallback_used=False
            )
