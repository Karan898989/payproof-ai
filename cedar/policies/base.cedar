// Cedar Policies for PayProof AI Pre-Payment Verification
// Defines roles: Analyst, Approver, Auditor, Admin

// Common: All active users can read cases and export dossiers
permit (
    principal in PayProof::Role::"Auditor",
    action in [PayProof::Action::"ReadCase", PayProof::Action::"ExportCase"],
    resource
);

// Analyst role: can create cases, upload evidence, and trigger analysis
permit (
    principal in PayProof::Role::"Analyst",
    action in [
        PayProof::Action::"CreateCase",
        PayProof::Action::"ReadCase",
        PayProof::Action::"UploadEvidence",
        PayProof::Action::"AnalyzeCase",
        PayProof::Action::"RequestVerification",
        PayProof::Action::"ExportCase"
    ],
    resource
);

// Explicit Analyst prohibition: Analysts can NEVER override holds or finalize payment disposition
forbid (
    principal in PayProof::Role::"Analyst",
    action in [
        PayProof::Action::"OverrideHold",
        PayProof::Action::"ApproveDisposition",
        PayProof::Action::"ManageBaseline"
    ],
    resource
);

// Approver role: can review, record callbacks, approve disposition, and override holds with reason
permit (
    principal in PayProof::Role::"Approver",
    action in [
        PayProof::Action::"ReadCase",
        PayProof::Action::"AnalyzeCase",
        PayProof::Action::"RequestVerification",
        PayProof::Action::"RecordVerification",
        PayProof::Action::"ApproveDisposition",
        PayProof::Action::"OverrideHold",
        PayProof::Action::"ExportCase"
    ],
    resource
);

// Admin role: full administrative privileges
permit (
    principal in PayProof::Role::"Admin",
    action,
    resource
);
