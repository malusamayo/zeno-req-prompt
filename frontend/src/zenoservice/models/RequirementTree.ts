import type { Requirement } from "./prompt";
export type RequirementTree = {
    feature: string;
    requirements: Array<{
        requirement: Requirement;
        color: string; // for category color
    }>;
};