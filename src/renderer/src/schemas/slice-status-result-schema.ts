import { array, nullable, number, object, string, tuple } from 'valibot'

const SliceStatusResultSchema = object({
	status: string('Status is required'),
	progress: array(
		tuple([string('Name is required'), number('Progress value is required')]),
		'Progress information is required'
	),
	error: nullable(string('Error is required'))
})

export default SliceStatusResultSchema
