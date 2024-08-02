import { array, number, object, InferOutput } from 'valibot'

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

export default ConfigurationJSONSchema
