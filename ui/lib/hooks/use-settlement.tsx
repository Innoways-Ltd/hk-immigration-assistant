import { SearchProgress } from "@/components/SearchProgress";
import { useCoAgent, useCoAgentStateRender } from "@copilotkit/react-core";
import { useCopilotChatSuggestions } from "@copilotkit/react-ui";
import { createContext, useContext, ReactNode, useMemo } from "react";
import { SettlementPlan, SettlementTask, AgentState } from "@/lib/types";

type SettlementContextType = {
  settlementPlan: SettlementPlan | null;
  selectedTaskId: string | null;
  selectedTask?: SettlementTask | null;
  customerInfo: any;
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

  useCoAgentStateRender<AgentState>({
    name: "immigration",
    render: ({ state }) => {
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

  return (
    <SettlementContext.Provider value={{ 
      settlementPlan: state.settlement_plan || null,
      selectedTaskId: state.selected_task_id || null,
      selectedTask,
      customerInfo: state.customer_info || {},
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
