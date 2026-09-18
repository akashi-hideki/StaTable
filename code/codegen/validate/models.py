# codegen/validate/models.py
"""\nValidation data model definitions\n"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional


class ValidationSeverity(Enum):
    """検証Severity"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    
    @classmethod
    def from_string(cls, value: str) -> 'ValidationSeverity':
        """Convert from string"""
        value_map = {
            'error': cls.ERROR,
            'warning': cls.WARNING,
            'info': cls.INFO,
            'ERROR': cls.ERROR,
            'WARNING': cls.WARNING,
            'INFO': cls.INFO,
            'Error': cls.ERROR,
            'Warning': cls.WARNING,
            'Info': cls.INFO,
        }
        return value_map.get(value, cls.INFO)


@dataclass
class ValidationIssue:
    """Validation issue"""
    category: str
    code: str
    message: str
    severity: ValidationSeverity
    target: str = ""
    suggestion: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'category': self.category,
            'code': self.code,
            'message': self.message,
            'severity': self.severity.value,
            'target': self.target,
            'suggestion': self.suggestion,
            'details': self.details,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ValidationIssue':
        """Restore from dictionary"""
        return cls(
            category=data.get('category', ''),
            code=data.get('code', ''),
            message=data.get('message', ''),
            severity=ValidationSeverity.from_string(data.get('severity', 'info')),
            target=data.get('target', ''),
            suggestion=data.get('suggestion', ''),
            details=data.get('details', {}),
        )
    
    def __str__(self) -> str:
        return f"[{self.severity.value.upper()}] {self.category}: {self.message}"


@dataclass
class ValidationResult:
    """Validation result"""
    issues: List[ValidationIssue] = field(default_factory=list)
    
    @property
    def passed(self) -> bool:
        return self.error_count == 0
    
    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ValidationSeverity.ERROR)
    
    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ValidationSeverity.WARNING)
    
    @property
    def info_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ValidationSeverity.INFO)
    
    def get_errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == ValidationSeverity.ERROR]
    
    def get_warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == ValidationSeverity.WARNING]
    
    def get_infos(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == ValidationSeverity.INFO]
    
    def get_by_category(self, category: str) -> List[ValidationIssue]:
        return [i for i in self.issues if i.category == category]
    
    def to_dict(self) -> Dict:
        return {
            'passed': self.passed,
            'error_count': self.error_count,
            'warning_count': self.warning_count,
            'info_count': self.info_count,
            'issues': [i.to_dict() for i in self.issues],
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ValidationResult':
        return cls(
            issues=[ValidationIssue.from_dict(i) for i in data.get('issues', [])]
        )
    
    def __str__(self) -> str:
        return (f"ValidationResult(errors={self.error_count}, "
                f"warnings={self.warning_count}, infos={self.info_count})")


@dataclass
class ValidationContext:
    """Validation context"""
    state_machine: Any = None
    global_defs: Any = None
    
    @property
    def states(self) -> Dict:
        return self.state_machine.states if self.state_machine else {}
    
    @property
    def events(self) -> Dict:
        return self.state_machine.events if self.state_machine else {}
    
    @property
    def transitions(self) -> List:
        return self.state_machine.transitions if self.state_machine else []
    
    @property
    def role_functions(self) -> Dict:
        return self.state_machine.role_functions if self.state_machine else {}
    
    @property
    def initial_state(self) -> Optional[str]:
        return self.state_machine.initial_state if self.state_machine else None
    
    @property
    def variables(self) -> List:
        return self.global_defs.variables if self.global_defs else []
    
    @property
    def flags(self) -> List:
        return self.global_defs.flags if self.global_defs else []
    
    @property
    def event_queues(self) -> List:
        return self.global_defs.event_queues if self.global_defs else []
    
    @property
    def interrupts(self) -> List:
        return self.global_defs.interrupts if self.global_defs else []
    
    @property
    def custom_types(self) -> List:
        return self.global_defs.custom_types if self.global_defs else []
    
    @property
    def timer_base(self):
        return self.global_defs.timer_base if self.global_defs else None
    
    @property
    def extra_timers(self) -> List:
        return self.global_defs.extra_timers if self.global_defs else []