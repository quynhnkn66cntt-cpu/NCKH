'use strict';

const { Contract } = require('fabric-contract-api');

class TraceabilityContract extends Contract {

    async InitLedger(ctx) {
        console.info('Traceability chaincode initialized');
    }

    _getMSPID(ctx) {
        return ctx.clientIdentity.getMSPID();
    }

    _validateWritePermission(mspID, eventType) {
        const permissions = {
            FarmMSP: [
                'SEED_STOCKING',
                'FEEDING',
                'TREATMENT',
                'HARVEST'
            ],
            ProcessingMSP: [
                'PROCESSING'
            ],
            DistributionMSP: [
                'SHIPPING',
                'DISTRIBUTION'
            ]
        };

        if (!permissions[mspID]) {
            throw new Error(`MSP ${mspID} is not authorized to create events`);
        }

        if (!permissions[mspID].includes(eventType)) {
            throw new Error(
                `MSP ${mspID} is not authorized to create event type ${eventType}`
            );
        }
    }

    async EventExists(ctx, eventID) {
        const data = await ctx.stub.getState(eventID);
        return !!data && data.length > 0;
    }

    async CreateEvent(
        ctx,
        eventID,
        batchID,
        eventType,
        actorID,
        dataHash,
        currentHash,
        previousEventHash,
        timestamp,
        documentURI
    ) {
        if (
            !eventID ||
            !batchID ||
            !eventType ||
            !actorID ||
            !dataHash ||
            !currentHash ||
            !previousEventHash ||
            !timestamp
        ) {
            throw new Error('Missing required event fields');
        }

        const exists = await this.EventExists(ctx, eventID);

        if (exists) {
            throw new Error(`Event ${eventID} already exists`);
        }

        const mspID = this._getMSPID(ctx);

        this._validateWritePermission(mspID, eventType);

        const txId = ctx.stub.getTxID();

        const event = {
            docType: 'traceabilityEvent',
            eventID,
            batchID,
            eventType,
            actorID,
            dataHash,
            currentHash,
            previousEventHash,
            timestamp,
            documentURI: documentURI || '',
            txId,
            createdByMSP: mspID
        };

        await ctx.stub.putState(
            eventID,
            Buffer.from(JSON.stringify(event))
        );

        const batchEventKey = ctx.stub.createCompositeKey(
            'batch~event',
            [batchID, eventID]
        );

        await ctx.stub.putState(batchEventKey, Buffer.from('\u0000'));

        return JSON.stringify(event);
    }

    async GetEvent(ctx, eventID) {
        const data = await ctx.stub.getState(eventID);

        if (!data || data.length === 0) {
            throw new Error(`Event ${eventID} does not exist`);
        }

        return data.toString();
    }

    async GetEventsByBatch(ctx, batchID) {
        const iterator = await ctx.stub.getStateByPartialCompositeKey(
            'batch~event',
            [batchID]
        );

        const events = [];

        while (true) {
            const result = await iterator.next();

            if (result.value && result.value.key) {
                const splitKey = ctx.stub.splitCompositeKey(
                    result.value.key
                );

                const eventID = splitKey.attributes[1];

                const eventData = await ctx.stub.getState(eventID);

                if (eventData && eventData.length > 0) {
                    events.push(JSON.parse(eventData.toString()));
                }
            }

            if (result.done) {
                await iterator.close();
                break;
            }
        }

        return JSON.stringify(events);
    }

    async VerifyEvent(ctx, eventID, expectedDataHash) {
        const data = await ctx.stub.getState(eventID);

        if (!data || data.length === 0) {
            throw new Error(`Event ${eventID} does not exist`);
        }

        const event = JSON.parse(data.toString());

        return JSON.stringify({
            eventID,
            storedDataHash: event.dataHash,
            expectedDataHash,
            valid: event.dataHash === expectedDataHash
        });
    }

    async GetEventHistory(ctx, eventID) {
        const iterator = await ctx.stub.getHistoryForKey(eventID);
        const history = [];

        while (true) {
            const result = await iterator.next();

            if (result.value) {
                history.push({
                    txId: result.value.txId,
                    timestamp: result.value.timestamp,
                    isDelete: result.value.isDelete,
                    value: result.value.value &&
                           result.value.value.length > 0
                        ? JSON.parse(result.value.value.toString())
                        : null
                });
            }

            if (result.done) {
                await iterator.close();
                break;
            }
        }

        return JSON.stringify(history);
    }
}

module.exports = TraceabilityContract;
