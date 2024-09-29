import type { VegaLiteSpec } from "svelte-vega";

export function generateSpec(parameters, selectMetrics): VegaLiteSpec {
	const x_encode = parameters.xEncoding;
	const y_encode = parameters.yEncoding;
	const z_encode = parameters.zEncoding;
	const paramMap = {
		metrics: {
			type: "quantitative",
			title: selectMetrics,
		},
		models: {
			type: "nominal",
			title: "models",
		},
		slices: {
			type: "nominal",
			title: "slices",
		},
	};
	const spec = {
		$schema: "https://vega.github.io/schema/vega-lite/v5.json",
		description: "A simple bar chart with embedded data.",
		autosize: "pad",
		width: {
			step: 30,
		},
		data: {
			name: "table",
		},
		encoding: {
			x: {
				title: paramMap[x_encode].title,
				field: x_encode,
				type: paramMap[x_encode].type,
				axis: {
					labelAngle: 45,
					labelFontSize: 14,
					titleFontSize: 14,
					titlePadding: 10,
				},
				sort: null,
			},
			y: {
				title: paramMap[y_encode].title,
				field: selectMetrics !== "slice size" ? y_encode : "size",
				type: paramMap[y_encode].type,
				axis: {
					labelFontSize: 14,
					titleFontSize: 14,
					titlePadding: 20,
				},
				sort: null,
			},
			xOffset: {
				field: z_encode,
				sort: null,
			},
			fillOpacity: {
				condition: { param: "highlight", value: 1, empty: false },
				value: 0.8,
			},
		},
		layer: [
			{
				params: [
					{
						name: "highlight",
						select: {
							type: "point",
							field: y_encode,
							on: "mouseover",
						},
					},
				],
				mark: {
					type: "bar",
					tooltip: {
						signal:
							"{'slice_name': datum.slices,'slice_size': datum.size, " +
							(selectMetrics !== "slice size" ? selectMetrics : "accuracy") +
							": datum.metrics, 'model': datum.models}",
					},
				},
				encoding: {
					color: {
						field: z_encode,
						sort: null,
						scale: { scheme: "category20" },
					},
				},
			},
			{
				mark: {
					type: "text",
					style: "label",
				},
				encoding: {
					text: {
						field: selectMetrics !== "slice size" ? y_encode : "size",
						type: paramMap[y_encode].type,
						format: paramMap[y_encode].type === "quantitative" ? ".2f" : "",
					},
				},
			},
		],
		config: {
			style: { label: { align: "center", dy: -5 } },
		},
	};

	return spec as VegaLiteSpec;
}

// export function generateStackedBarChartSpec(data): VegaLiteSpec {
// 	const spec = {
// 		width: 70,
// 		height: 15,
// 		mark: { type: "bar", orient: "horizontal" }, // Use 'horizontal' for a horizontal stacked bar
// 		encoding: {
// 			x: {
// 				field: "value", // The quantitative field to be stacked
// 				type: "quantitative",
// 				title: "",
// 				axis: null,
// 				stack: true, // Enable stacking
// 			},
// 			color: {
// 				field: "category", // The categorical field to distinguish the stack segments
// 				type: "nominal",
// 				scale: {
// 					// Define custom colors for categories
// 					domain: ["Pass", "Fail"],
// 					range: ["#97ca00", "#e05d44"],
// 				},
// 				legend: null, // Disable the legend for the category field
// 			},
// 			tooltip: [
// 				// Tooltip shows the category and value
// 				{ field: "category", type: "nominal" },
// 				{ field: "value", type: "quantitative" },
// 			],
// 		},
// 		data: { values: data }, // Input data for the chart
// 		selection: {
// 			// Add interactivity with selection
// 			barSelect: {
// 				type: "single",
// 				on: "click",
// 				fields: ["category"],
// 				empty: "none",
// 			},
// 		},
// 	};

// 	return spec as VegaLiteSpec;
// }

export function generateStackedBarChartSpec(data): VegaLiteSpec {
	const spec = {
		width: 70,
		height: 15,
		mark: { type: "bar", orient: "horizontal" }, // Use 'horizontal' for a horizontal stacked bar
		encoding: {
			x: {
				field: "value", // The quantitative field to be stacked
				type: "quantitative",
				title: "",
				axis: null,
				stack: true, // Enable stacking
			},
			color: {
				field: "category", // The categorical field to distinguish the stack segments
				type: "nominal",
				scale: {
					// Define custom colors for categories
					domain: ["Pass", "Fail"],
					range: ["#97ca00", "#e05d44"],
				},
				legend: null, // Disable the legend for the category field
			},
			tooltip: [
				// Tooltip shows the category and value
				{ field: "category", type: "nominal" },
				{ field: "value", type: "quantitative" },
			],
		},
		data: { values: data }, // Input data for the chart
		selection: {
            barSelect: {
                type: "single",
                on: "click",
                fields: ["category"],
                empty: "none"
            }
        }
	};

	return spec as VegaLiteSpec;
}