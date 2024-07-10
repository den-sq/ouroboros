import { array, nullable, number, object, string } from 'valibot'

const SliceVisualizationResultSchema = object(
	{
		data: nullable(
			object({
				rects: array(array(array(number()))),
				bounding_boxes: array(
					object({
						min: array(number()),
						max: array(number())
					})
				),
				link_rects: array(number())
			})
		),
		error: nullable(string())
	},
	'The data provided for slice visualization is invalid.'
)

export default SliceVisualizationResultSchema
