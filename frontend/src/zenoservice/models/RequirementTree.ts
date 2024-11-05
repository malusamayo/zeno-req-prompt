import type { Requirement } from "./prompt";
export type RequirementTree = {
	feature: string;
	requirements: Array<{
		requirement: Requirement;
		suggested: boolean;
	}>;
	showNewRequirement: boolean;
};
