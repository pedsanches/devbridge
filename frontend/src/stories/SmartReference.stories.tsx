import type { Meta, StoryObj } from '@storybook/react';
import { SmartReference, ReferenceType } from "@/components/ui/SmartReference";

const meta = {
    title: 'UI/SmartReference',
    component: SmartReference,
    parameters: {
        layout: 'centered',
    },
    tags: ['autodocs'],
} satisfies Meta<typeof SmartReference>;

export default meta;
type Story = StoryObj<typeof meta>;

// 1. Standard PR (Full Payload)
export const FullPullRequest: Story = {
    args: {
        id: "R1",
        source: {
            ref_id: "R1",
            external_id: "PR #1234",
            title: "feat(auth): Add magic link login support",
            repository: "devbridge/backend",
            type: ReferenceType.PULL_REQUEST,
            url: "https://github.com/example/repo/pull/123",
            description: "Implements the core logic for passwordless auth.",
            author: { name: "Pedro", avatarUrl: "" },
            status: "merged"
        }
    },
};

// 2. Issue (Minimal Payload)
export const MinimalIssue: Story = {
    args: {
        id: "R2",
        source: {
            ref_id: "R2",
            external_id: "ISS-450",
            title: "Fix memory leak in worker",
            type: ReferenceType.ISSUE,
            url: "https://jira.com/ISS-450"
        }
    },
};

// 3. Unknown Type (Robustness Test)
export const UnknownType: Story = {
    args: {
        id: "R3",
        source: {
            ref_id: "R3",
            external_id: "TICKET-999",
            title: "Legacy system ticket",
            type: "jira_ticket", // Intentionally unknown string
            url: "#",
            description: "Should fallback to generic link icon"
        }
    },
};

// 4. Missing Optional Fields (Robustness Test)
export const MissingFields: Story = {
    args: {
        id: "R4",
        source: {
            ref_id: "R4",
            title: "", // Empty title should fallback to ID/ExternalID
            type: ReferenceType.DOC,
            // No URL, No Author, No Status
        }
    },
};

// 5. Not Found (Fallback)
export const NotFound: Story = {
    args: {
        id: "R99",
        source: undefined
    },
};
