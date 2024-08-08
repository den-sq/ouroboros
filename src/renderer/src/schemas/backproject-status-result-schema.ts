import { array, nullable, number, object, string, tuple } from 'valibot'
import { baseParse } from './schema-helpers'

const BackprojectStatusResultSchema = object({
	status: string('Status is required'),
	progress: array(
		tuple([
			string('Name is required'),
			number('Progress value is required'),
			number('Duration is required')
		]),
		'Progress information is required'
	),
	error: nullable(string('Error is required'))
})

export const parseBackprojectStatusResult = baseParse(
	BackprojectStatusResultSchema,
	'Invalid backproject status result'
)

export default BackprojectStatusResultSchema
