import { SearchProgress } from "@/components/SearchProgress";
import { useCoAgent, useCoAgentStateRender } from "@copilotkit/react-core";
import { useCopilotChatSuggestions } from "@copilotkit/react-ui";
import { createContext, useContext, ReactNode, useMemo, useState, useCallback } from "react";
import { SettlementPlan, SettlementTask, AgentState, ServiceLocation } from "@/lib/types";
import { Card } from "@/components/ui/card";
import { LoaderCircle } from "lucide-react";

type SettlementContextType = {
  settlementPlan: SettlementPlan | null;
  selectedTaskId: string | null;
  selectedTask?: SettlementTask | null;
  customerInfo: any;
  hoveredDay: number | null;
  hoveredTaskId: string | null;
  setHoveredDay: (day: number | null) => void;
  setHoveredTaskId: (taskId: string | null) => void;
  focusedLocations: ServiceLocation[];
  completedTasks: Set<string>;
  toggleTaskCompletion: (taskId: string) => void;
};

const SettlementContext = createContext<SettlementContextType | undefined>(undefined);

export const SettlementProvider = ({ children }: { children: ReactNode }) => {
  const { state } = useCoAgent<AgentState>({
    name: "immigration",
    initialState: {
      customer_info: {},
      settlement_plan: null,
      selected_task_id: null,
    },
  });

  // Map interaction states
  const [hoveredDay, setHoveredDay] = useState<number | null>(null);
  const [hoveredTaskId, setHoveredTaskId] = useState<string | null>(null);
  
  // Task completion state
  const [completedTasks, setCompletedTasks] = useState<Set<string>>(new Set());

  useCoAgentStateRender<AgentState>({
    name: "immigration",
    render: ({ state }) => {
      if (state.planning_progress && state.planning_progress.length > 0) {
        const latestProgress = state.planning_progress[state.planning_progress.length - 1];
        if (!latestProgress.done) {
          return (
            <Card className="p-4 flex items-center gap-2">
              <LoaderCircle className="w-4 h-4 text-blue-500 bg-blue-500/20 rounded-full p-1 animate-spin" />
              <p className="text-sm font-medium">
                正在创建您的安家计划，请稍候...
              </p>
            </Card>
          );
        }
      }
      if (state.search_progress && state.search_progress.length > 0) {
        return <SearchProgress progress={state.search_progress} />
      }
      return null;
    },
  });

  useCopilotChatSuggestions({
    instructions: `Offer the user actionable suggestions based on their settlement plan and current progress.\n ${JSON.stringify(state.settlement_plan)}`,
    minSuggestions: 1,
    maxSuggestions: 2,
  }, [state.settlement_plan]);

  const selectedTask = useMemo(() => {
    if (!state.selected_task_id || !state.settlement_plan) return null;
    return state.settlement_plan.tasks?.find((task: SettlementTask) => task.id === state.selected_task_id);
  }, [state.settlement_plan, state.selected_task_id]);

  // Calculate focused locations based on hovered day or task
  const focusedLocations = useMemo(() => {
    if (!state.settlement_plan) return [];

    // If hovering on a specific task, show only that task's location
    if (hoveredTaskId) {
      const task = state.settlement_plan.tasks?.find((t: SettlementTask) => t.id === hoveredTaskId);
      console.log('[DEBUG] Hovered task:', task?.title, 'Has location:', !!task?.location);
      if (task?.location) {
        console.log('[DEBUG] Task location:', task.location.name, 'Lat:', task.location.latitude, 'Lng:', task.location.longitude);
      }
      if (task && task.location) {
        return [task.location];
      }
      return [];
    }

    // If hovering on a day, show all locations for tasks on that day
    if (hoveredDay !== null) {
      console.log('[DEBUG] Hovering on day:', hoveredDay);
      const tasksOnDay = state.settlement_plan.tasks?.filter((task: SettlementTask) => {
        // Parse day_range which can be "Day 1", "Day 1 (Jul 10)", or "Day 1-3 (Jul 10 - Jul 12)"
        const dayMatch = task.day_range.match(/Day (\d+)/);
        if (!dayMatch) return false;
        const taskDay = parseInt(dayMatch[1]);
        const matches = taskDay === hoveredDay;
        console.log(`[DEBUG] Task "${task.title}" day_range="${task.day_range}" taskDay=${taskDay} matches=${matches} hasLocation=${!!task.location}`);
        return matches;
      }) || [];
      console.log('[DEBUG] Tasks on day:', tasksOnDay.length);

      const locations = tasksOnDay
        .map((task: SettlementTask) => task.location)
        .filter((loc): loc is ServiceLocation => loc !== null && loc !== undefined);

      console.log('[DEBUG] Locations found on day', hoveredDay, ':', locations.length, locations.map(l => l?.name));
      return locations;
    }

    // Default: show Day 1 locations only
    if (state.settlement_plan.tasks && state.settlement_plan.tasks.length > 0) {
      const day1Tasks = state.settlement_plan.tasks.filter((task: SettlementTask) => {
        const dayMatch = task.day_range.match(/Day (\d+)/);
        return dayMatch && parseInt(dayMatch[1]) === 1;
      });
      
      const day1Locations = day1Tasks
        .map((task: SettlementTask) => task.location)
        .filter((loc): loc is ServiceLocation => loc !== null && loc !== undefined);
      
      if (day1Locations.length > 0) {
        return day1Locations;
      }
    }
    
    // Fallback: show all locations if no Day 1 tasks found
    return state.settlement_plan.service_locations || [];
  }, [state.settlement_plan, hoveredDay, hoveredTaskId]);

  // Toggle task completion
  const toggleTaskCompletion = useCallback((taskId: string) => {
    setCompletedTasks(prev => {
      const newSet = new Set(prev);
      if (newSet.has(taskId)) {
        newSet.delete(taskId);
      } else {
        newSet.add(taskId);
      }
      return newSet;
    });
  }, []);

  return (
    <SettlementContext.Provider value={{ 
      settlementPlan: state.settlement_plan || null,
      selectedTaskId: state.selected_task_id || null,
      selectedTask,
      customerInfo: state.customer_info || {},
      hoveredDay,
      hoveredTaskId,
      setHoveredDay,
      setHoveredTaskId,
      focusedLocations,
      completedTasks,
      toggleTaskCompletion,
    }}>
      {children}
    </SettlementContext.Provider>
  );
};

export const useSettlement = () => {
  const context = useContext(SettlementContext);
  if (context === undefined) {
    throw new Error("useSettlement must be used within a SettlementProvider");
  }
  return context;
};
