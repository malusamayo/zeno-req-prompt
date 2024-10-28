import type { Requirement } from "./prompt";
export type OptimizeRequirement = {
    promptId: string;
    requirement: {
        id: string;
        name: string;
        description: string;
        promptSnippet: string;
        evaluationMethod: string;
    };
};