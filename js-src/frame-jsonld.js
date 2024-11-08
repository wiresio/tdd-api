/********************************************************************************
 * Copyright (c) 2018 Contributors to the Eclipse Foundation
 *
 * See the NOTICE file(s) distributed with this work for additional
 * information regarding copyright ownership.
 *
 * This program and the accompanying materials are made available under the
 * terms of the Eclipse Public License v. 2.0 which is available at
 * http://www.eclipse.org/legal/epl-2.0, or the W3C Software Notice and
 * Document License (2015-05-13) which is available at
 * https://www.w3.org/Consortium/Legal/2015/copyright-software-and-document.
 *
 * SPDX-License-Identifier: EPL-2.0 OR W3C-20150513
 **********************************************************************************/

import { fromRDF, frame as jsonldFrame } from "jsonld";
import fs from "fs";

const dataFilePath = process.argv[2];
const framedata = process.argv[3];

async function frame() {
  const data = fs.readFileSync(dataFilePath, "utf-8");
  const doc = await fromRDF(data, {
    format: "application/n-quads",
    useNativeTypes: "true",
  });
  const framed = await jsonldFrame(doc, JSON.parse(framedata));
  return JSON.stringify(framed, null, 2);
}

frame().then(console.log);
