import { useEffect, useRef } from 'react'
import styles from './DynamicIcon.module.css'
import { Location } from 'react-router-dom'

function DynamicIcon({
	url,
	location,
	path
}: {
	url: string
	location: Location
	path: string
}): JSX.Element {
	const active = location.pathname ? location.pathname.includes(path) : false
	const activeStyle = active ? styles.dynamicIconActive : ''

	const ref = useRef<HTMLDivElement>(null)

	useEffect(() => {
		if (ref.current) {
			ref.current.style.maskRepeat = 'no-repeat'
			ref.current.style.maskPosition = 'center'
			ref.current.style.maskImage = `url(${url})`
		}
	}, [url])

	return <div ref={ref} className={`${styles.dynamicIcon} ${activeStyle}`}></div>
}

export default DynamicIcon
