import { array, number, object, InferOutput } from 'valibot'
import { baseParse, makeErrorResult, makeSuccessResult, ParseResult } from './schema-helpers'
import { VisualizationOutput } from '@renderer/routes/SlicesPage/components/VisualizeSlicing/VisualizeSlicing'
import { visualizationDataToOutputFormat } from './slice-visualization-result-schema'

const ConfigurationJSONSchema = object({
	slice_rects: array(array(array(number()))),
	volume_cache: object({
		bounding_boxes: array(
			object({
				x_min: number(),
				x_max: number(),
				y_min: number(),
				y_max: number(),
				z_min: number(),
				z_max: number()
			})
		),
		link_rects: array(number())
	})
})

export type ConfigurationJSON = InferOutput<typeof ConfigurationJSONSchema>

export const parseConfigurationJSON = baseParse(
	ConfigurationJSONSchema,
	'Invalid configuration JSON'
)

export const parseConfigurationJSONToOutputFormat = (
	input: object | null
): ParseResult<VisualizationOutput> => {
	const { result, error } = parseConfigurationJSON(input)

	if (error) {
		return makeErrorResult(error)
	}

	return makeSuccessResult(convertConfigJSONToOutputFormat(result))
}

export function convertConfigJSONToOutputFormat(
	configJSON: ConfigurationJSON
): VisualizationOutput {
	const rects = configJSON.slice_rects
	const boundingBoxes = configJSON.volume_cache.bounding_boxes.map((box) => {
		return { min: [box.x_min, box.y_min, box.z_min], max: [box.x_max, box.y_max, box.z_max] }
	})
	const linkRects = configJSON.volume_cache.link_rects

	return visualizationDataToOutputFormat({
		rects,
		bounding_boxes: boundingBoxes,
		link_rects: linkRects
	})!
}

export default ConfigurationJSONSchema
