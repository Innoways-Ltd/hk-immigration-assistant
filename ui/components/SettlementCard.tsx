import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useSettlement } from "@/lib/hooks/use-settlement";
import { SettlementTask } from "@/lib/types";
import { CheckCircle2, Circle, Clock, MapPin } from "lucide-react";
import { cn } from "@/lib/utils";

export function SettlementCard({ className }: { className?: string }) {
  const { settlementPlan, customerInfo } = useSettlement();

  if (!settlementPlan) {
    return (
      <Card className={cn("overflow-hidden", className)}>
        <CardHeader>
          <CardTitle>Settlement Plan</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            No settlement plan created yet. Share your information to get started.
          </p>
        </CardContent>
      </Card>
    );
  }

  const groupTasksByPhase = (tasks: SettlementTask[]) => {
    const phases: { [key: string]: SettlementTask[] } = {
      "Arrival & Temporary Settlement (Day 1-3)": [],
      "Housing (Day 3-7)": [],
      "Banking & Identity (Day 7-14)": [],
      "Work & Daily Life (Day 14-30)": [],
    };

    tasks.forEach((task) => {
      if (task.day_range.includes("Day 1") || task.day_range.includes("Day 2") || task.day_range.includes("Day 3")) {
        phases["Arrival & Temporary Settlement (Day 1-3)"].push(task);
      } else if (task.day_range.includes("Day 3") || task.day_range.includes("Day 5") || task.day_range.includes("Day 7")) {
        phases["Housing (Day 3-7)"].push(task);
      } else if (task.day_range.includes("Day 7") || task.day_range.includes("Day 10") || task.day_range.includes("Day 14")) {
        phases["Banking & Identity (Day 7-14)"].push(task);
      } else {
        phases["Work & Daily Life (Day 14-30)"].push(task);
      }
    });

    return phases;
  };

  const phases = groupTasksByPhase(settlementPlan.tasks);

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "high":
        return "text-red-500";
      case "medium":
        return "text-yellow-500";
      case "low":
        return "text-green-500";
      default:
        return "text-gray-500";
    }
  };

  return (
    <Card className={cn("overflow-hidden flex flex-col", className)}>
      <CardHeader className="border-b">
        <CardTitle className="text-lg">
          {customerInfo.name ? `${customerInfo.name}'s ` : ""}Settlement Plan
        </CardTitle>
        {customerInfo.arrival_date && (
          <p className="text-sm text-muted-foreground">
            Arriving: {customerInfo.arrival_date}
          </p>
        )}
      </CardHeader>
      <CardContent className="flex-1 overflow-y-auto p-4 space-y-6">
        {Object.entries(phases).map(([phaseName, tasks]) => {
          if (tasks.length === 0) return null;
          
          return (
            <div key={phaseName} className="space-y-2">
              <h3 className="font-semibold text-sm text-primary">{phaseName}</h3>
              <div className="space-y-2">
                {tasks.map((task) => (
                  <div
                    key={task.id}
                    className="border rounded-lg p-3 hover:bg-accent transition-colors cursor-pointer"
                  >
                    <div className="flex items-start gap-2">
                      <div className="mt-0.5">
                        {task.status === "completed" ? (
                          <CheckCircle2 className="h-4 w-4 text-green-500" />
                        ) : (
                          <Circle className="h-4 w-4 text-muted-foreground" />
                        )}
                      </div>
                      <div className="flex-1 space-y-1">
                        <div className="flex items-center justify-between">
                          <h4 className="font-medium text-sm">{task.title}</h4>
                          <span className={cn("text-xs font-medium", getPriorityColor(task.priority))}>
                            {task.priority}
                          </span>
                        </div>
                        <p className="text-xs text-muted-foreground">{task.description}</p>
                        <div className="flex items-center gap-3 text-xs text-muted-foreground">
                          <div className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            <span>{task.day_range}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            <span>{task.estimated_duration}</span>
                          </div>
                          {task.location && (
                            <div className="flex items-center gap-1">
                              <MapPin className="h-3 w-3" />
                              <span>{task.location.name}</span>
                            </div>
                          )}
                        </div>
                        {task.documents_needed.length > 0 && (
                          <div className="text-xs">
                            <span className="font-medium">Documents: </span>
                            <span className="text-muted-foreground">
                              {task.documents_needed.join(", ")}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
