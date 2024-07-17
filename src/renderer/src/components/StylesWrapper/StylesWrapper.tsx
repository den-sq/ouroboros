function StylesWrapper({
	children,
	stylesPath
}: {
	children: React.ReactNode
	stylesPath: string | undefined
}): JSX.Element {
	return (
		<>
			{stylesPath ? <link rel="stylesheet" type="text/css" href={stylesPath} /> : null}
			{children}
		</>
	)
}

export default StylesWrapper
