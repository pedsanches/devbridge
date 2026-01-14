"use client";

import { Users } from "lucide-react";
import { PageLayout } from "@/components/layout/PageLayout";
import { TeamsManager } from "@/components/teams/TeamsManager";

export default function TeamsPage() {
    return (
        <PageLayout
            title="Gestão de Times"
            subtitle="Gerencie seus times e os repositórios associados a eles"
            icon={Users}
        >
            <TeamsManager />
        </PageLayout>
    );
}
