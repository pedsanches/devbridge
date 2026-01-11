import { TeamsManager } from "@/components/teams/TeamsManager";

export default function TeamsPage() {
    return (
        <div className="container mx-auto space-y-8 p-8">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Gestão de Times</h1>
                <p className="text-muted-foreground">
                    Gerencie seus times e os repositórios associados a eles.
                </p>
            </div>
            <TeamsManager />
        </div>
    );
}
