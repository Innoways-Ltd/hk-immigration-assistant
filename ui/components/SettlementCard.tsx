import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useSettlement } from "@/lib/hooks/use-settlement";
import { SettlementTask } from "@/lib/types";
import { CheckCircle2, Circle, Clock, MapPin, Calendar, FileText, Mail, Star, Lightbulb, X, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useState } from "react";

export function SettlementCard({ className }: { className?: string }) {
  const { 
    settlementPlan, 
    customerInfo, 
    setHoveredDay, 
    setHoveredTaskId,
    completedTasks,
    toggleTaskCompletion
  } = useSettlement();
  
  const [isSendingEmail, setIsSendingEmail] = useState(false);

  if (!settlementPlan) {
    return null; // Don't show empty card
  }

  /**
   * Extract day number from day_range string
   * Examples: "Day 1", "Day 1-2", "Day 1 (Jun 01)", "Day 1-2 (Jun 01 - Jun 02)"
   */
  const extractDayNumber = (dayRange: string): number | null => {
    const match = dayRange.match(/Day (\d+)/);
    return match ? parseInt(match[1]) : null;
  };

  /**
   * Extract day range (start and end) from day_range string
   * IMPORTANT: Only return the START day to avoid duplicates
   */
  const extractStartDay = (dayRange: string): number | null => {
    const match = dayRange.match(/Day (\d+)/);
    return match ? parseInt(match[1]) : null;
  };

  /**
   * Group tasks by their START day only (no duplicates)
   */
  const groupTasksByDay = (tasks: SettlementTask[]): { [day: number]: SettlementTask[] } => {
    const dayMap: { [day: number]: SettlementTask[] } = {};

    tasks.forEach((task) => {
      const startDay = extractStartDay(task.day_range);
      if (startDay === null) return;

      // Add task only to its start day
      if (!dayMap[startDay]) {
        dayMap[startDay] = [];
      }
      dayMap[startDay].push(task);
    });

    return dayMap;
  };

  /**
   * Get the maximum day number from all tasks
   */
  const getMaxDay = (tasks: SettlementTask[]): number => {
    let maxDay = 0;
    tasks.forEach((task) => {
      const startDay = extractStartDay(task.day_range);
      if (startDay && startDay > maxDay) {
        maxDay = startDay;
      }
    });
    return maxDay;
  };

  const tasksByDay = groupTasksByDay(settlementPlan.tasks);
  const maxDay = getMaxDay(settlementPlan.tasks);
  const days = Array.from({ length: maxDay }, (_, i) => i + 1);

  const getPriorityBadge = (priority: string) => {
    const baseClasses = "text-xs px-2 py-0.5 rounded-full font-medium";
    switch (priority) {
      case "high":
        return `${baseClasses} bg-red-100 text-red-700`;
      case "medium":
        return `${baseClasses} bg-yellow-100 text-yellow-700`;
      case "low":
        return `${baseClasses} bg-green-100 text-green-700`;
      default:
        return `${baseClasses} bg-gray-100 text-gray-700`;
    }
  };

  /**
   * Extract date string from day_range if available
   * Example: "Day 1 (Jun 01)" -> "Jun 01"
   */
  const extractDateString = (dayRange: string): string | null => {
    const match = dayRange.match(/\(([^)]+)\)/);
    if (!match) return null;
    // If it's a range like "Jun 01 - Jun 03", extract the start date
    const dateStr = match[1];
    const startDate = dateStr.split(' - ')[0];
    return startDate;
  };

  /**
   * Get date string for a specific day by looking at tasks on that day
   */
  const getDateForDay = (day: number, tasks: SettlementTask[]): string | null => {
    const tasksOnDay = tasks.filter(task => {
      const startDay = extractStartDay(task.day_range);
      return startDay === day;
    });

    for (const task of tasksOnDay) {
      const dateStr = extractDateString(task.day_range);
      if (dateStr) return dateStr;
    }

    return null;
  };

  /**
   * Send selected tasks to email
   */
  const handleSendToEmail = async () => {
    if (completedTasks.size === 0) {
      alert("Please select at least one task to send.");
      return;
    }

    setIsSendingEmail(true);

    try {
      const selectedTasksList = settlementPlan.tasks.filter(task => 
        completedTasks.has(task.id)
      );

      // Format tasks for email
      const emailContent = selectedTasksList.map(task => {
        const docs = task.documents_needed && task.documents_needed.length > 0
          ? `\nDocuments needed: ${task.documents_needed.join(', ')}`
          : '';
        
        return `
${task.title}
Day: ${task.day_range}
Priority: ${task.priority}
Description: ${task.description}
Duration: ${task.estimated_duration}${docs}
${task.location ? `Location: ${task.location.name} - ${task.location.address}` : ''}
        `.trim();
      }).join('\n\n---\n\n');

      const subject = `${customerInfo.name || 'Your'} Settlement Plan - Selected Tasks`;
      const body = `Hi ${customerInfo.name || 'there'},\n\nHere are your selected settlement tasks:\n\n${emailContent}\n\nBest regards,\nHK Immigration Assistant`;

      // Create mailto link
      const mailtoLink = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
      window.location.href = mailtoLink;

      // Alternative: You can also implement a backend API call here
      // const response = await fetch('/api/send-email', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({
      //     to: customerInfo.email,
      //     subject,
      //     body: emailContent
      //   })
      // });

    } catch (error) {
      console.error('Error sending email:', error);
      alert('Failed to send email. Please try again.');
    } finally {
      setIsSendingEmail(false);
    }
  };

  return (
    <Card className={cn("overflow-hidden flex flex-col backdrop-blur-md bg-white/80 border-white/20", className)}>
      <CardHeader className="border-b">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-lg">
              {customerInfo.name ? `${customerInfo.name}'s ` : ""}Settlement Plan
            </CardTitle>
            {settlementPlan.tasks.length > 0 && (
              <p className="text-xs text-muted-foreground">
                {maxDay} days • {settlementPlan.tasks.length} tasks
              </p>
            )}
            {customerInfo.arrival_date && (
              <p className="text-sm text-muted-foreground">
                Arriving: {customerInfo.arrival_date}
              </p>
            )}
          </div>
          
          {/* Send to Email Button */}
          <Button
            size="sm"
            variant="outline"
            onClick={handleSendToEmail}
            disabled={isSendingEmail || completedTasks.size === 0}
            className="flex items-center gap-1"
          >
            <Mail className="w-4 h-4" />
            <span className="hidden sm:inline">Send</span>
          </Button>
        </div>
      </CardHeader>
      
      <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
        {days.map((day) => {
          const tasksOnDay = tasksByDay[day] || [];
          
          if (tasksOnDay.length === 0) {
            return null;
          }

          const dateStr = getDateForDay(day, settlementPlan.tasks);

          return (
            <div 
              key={day} 
              className="space-y-3"
              onMouseEnter={() => setHoveredDay(day)}
              onMouseLeave={() => setHoveredDay(null)}
            >
              {/* Day Header */}
              <div className="flex items-center gap-2 pb-2 border-b">
                <Calendar className="w-4 h-4 text-primary" />
                <h3 className="font-semibold text-sm">
                  Day {day}
                  {dateStr && <span className="text-muted-foreground ml-2">({dateStr})</span>}
                </h3>
              </div>

              {/* Tasks for this day */}
              <div className="space-y-2 pl-2">
                {tasksOnDay.map((task) => {
                  const isCompleted = completedTasks.has(task.id);
                  
                  return (
                    <div
                      key={task.id}
                      className="group p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors cursor-pointer"
                      onMouseEnter={() => setHoveredTaskId(task.id)}
                      onMouseLeave={() => setHoveredTaskId(null)}
                      onClick={() => toggleTaskCompletion(task.id)}
                    >
                      <div className="flex items-start gap-3">
                        {/* Checkbox Icon */}
                        <div className="mt-0.5 cursor-pointer">
                          {isCompleted ? (
                            <CheckCircle2 className="w-5 h-5 text-green-500" />
                          ) : (
                            <Circle className="w-5 h-5 text-gray-400 group-hover:text-gray-600" />
                          )}
                        </div>

                        {/* Task Content */}
                        <div className="flex-1 min-w-0 space-y-1">
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex items-center gap-2">
                              {/* Task Type Icon */}
                              {task.task_type === "extended" ? (
                                <Lightbulb className="w-4 h-4 text-blue-500 flex-shrink-0" title="AI Suggested" />
                              ) : (
                                <Star className="w-4 h-4 text-amber-500 flex-shrink-0" title="Essential Task" />
                              )}
                              <h4 className="font-medium text-sm leading-tight">
                                {task.title}
                              </h4>
                            </div>
                            <span className={getPriorityBadge(task.priority)}>
                              {task.priority}
                            </span>
                          </div>

                          <p className="text-xs text-muted-foreground line-clamp-2">
                            {task.description}
                          </p>

                          {/* Recommendation Reason for Extended Tasks */}
                          {task.task_type === "extended" && task.recommendation_reason && (
                            <div className="bg-blue-50 border border-blue-200 rounded-md p-2 mt-2">
                              <p className="text-xs text-blue-700">
                                <span className="font-semibold">Why recommended: </span>
                                {task.recommendation_reason}
                              </p>
                            </div>
                          )}

                          {/* Task Details */}
                          <div className="flex flex-wrap gap-3 text-xs text-muted-foreground pt-1">
                            {task.estimated_duration && (
                              <div className="flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                <span>{task.estimated_duration}</span>
                              </div>
                            )}

                            {task.location && (
                              <div className="flex items-center gap-1">
                                <MapPin className="w-3 h-3" />
                                <span className="truncate">{task.location.name}</span>
                              </div>
                            )}

                            {task.documents_needed && task.documents_needed.length > 0 && (
                              <div className="flex items-center gap-1 flex-wrap">
                                <FileText className="w-3 h-3" />
                                <span className="text-xs">
                                  {task.documents_needed.join(', ')}
                                </span>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
